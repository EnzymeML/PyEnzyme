'''
File: template.py
Project: restful
Author: Jan Range
License: BSD-2 clause
-----
Last Modified: Wednesday June 23rd 2021 9:57:02 pm
Modified By: Jan Range (<jan.range@simtech.uni-stuttgart.de>)
-----
Copyright (c) 2021 Institute of Biochemistry and Technical Biochemistry Stuttgart
'''

from flask import request, send_file, jsonify
from flask_apispec import doc, marshal_with, MethodResource

import os
import shutil
import io

from pyenzyme.enzymeml.tools import UnitCreator
from pyenzyme.enzymeml.core import \
    Replicate, EnzymeMLDocument, EnzymeReaction,\
    Vessel, Protein, Reactant, Creator
from pyenzyme.restful.template_schema import TemplateSchema

from builtins import enumerate

import tempfile
import numpy as np
import pandas as pd

desc = 'This endpoint is used to convert an EnzymeML-Template spreadsheet to \
        an EnzymeML OMEX container.\
        Upload your XLSM file using form-data with the "xlsm" tag. \
        The endpoint will return the converted template as an OMEX file.'


class convertTemplate(MethodResource):

    @doc(tags=['Convert EnzymeML-Template'], description=desc)
    @marshal_with(TemplateSchema(), code=200)
    def post(self):

        # check if the post request has the file part
        if 'xlsm' not in request.files:
            return jsonify(
                {"response": 'No file part'}
            )

        file = request.files['xlsm']

        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            return jsonify(
                {"response": 'No file selected'}
            )

        if file and file.filename.split('.')[-1] in "xlsm_xlsx":

            file.seek(0)
            enzmldoc = self.convertSheet(file)

            # Send File
            dirpath = os.path.join(
                os.path.dirname(os.path.realpath(__file__)),
                "converter_temp"
            )

            os.makedirs(dirpath, exist_ok=True)
            dirpath = os.path.join(
                dirpath,
                next(tempfile._get_candidate_names())
            )

            enzmldoc.toFile(dirpath)

            path = os.path.join(
                dirpath,
                enzmldoc.getName().replace(' ', '_') + '.omex'
            )

            f = io.BytesIO(open(path, "rb").read())
            f.name = enzmldoc.getName() + '.omex'

            shutil.rmtree(dirpath, ignore_errors=True)

            return send_file(
                f,
                mimetype='omex',
                as_attachment=True,
                attachment_filename='%s.omex' % enzmldoc.getName())

    def convertSheet(self, file):

        # gather sheets by name
        sheets = self.getSheets(file)

        # General information
        info = self.getGeneralInfo(sheets["generalInfo"])
        doc = info["doc"]
        info.pop("doc")

        enzmldoc = EnzymeMLDocument(**info)
        enzmldoc.setCreated(str(doc))

        # Creators
        self.getCreators(sheets['creator'], enzmldoc)

        # create mapping dictionary
        self.proteinDict = dict()
        self.reactantDict = dict()

        # Vessel
        self.getVessels(sheets["vessels"], enzmldoc)

        # Reactants
        self.getReactants(sheets["reactants"], enzmldoc)

        # Proteins
        self.getProteins(sheets["proteins"], enzmldoc)

        # Reactions
        self.getReactions(sheets["reactions"], enzmldoc)

        # Data
        self.getData(sheets["data"], enzmldoc)

        return enzmldoc

    def __cleanSpaces(self, cell):
        if cell == " ":
            return np.nan
        else:
            return cell

    def getSheets(self, file):

        def loadSheet(name, skiprow):
            return pd.read_excel(
                file,
                sheet_name=name,
                skiprows=skiprow
            )

        return {
            "creator": loadSheet("General Information", 9),
            "generalInfo": loadSheet("General Information", 1),
            "vessels": loadSheet("Vessels", 2),
            "reactants": loadSheet("Reactants", 2),
            "proteins": loadSheet("Proteins", 2),
            "reactions": loadSheet("Reactions", 2),
            "kineticModels": loadSheet("Kinetic Models", 2),
            "data": loadSheet("Data", 3),
        }

    def getCreators(self, sheet, enzmldoc):

        sheet = sheet.iloc[:, 0:3].dropna()
        sheet.columns = ["family_name", "given_name", "mail"]
        data = sheet.to_dict("index")

        creators = [Creator(**user) for user in data.values()]

        enzmldoc.setCreator(creators)

    def getGeneralInfo(self, sheet):

        sheet = sheet.replace(np.nan, '#NULL#', regex=True)
        data = dict()

        def addData(name, val, d):
            return d.update({name: val}) if val != "#NULL#" else False

        keys = ["name", "doc", "doi", "pubmedID", "url"]

        for i, name in enumerate(keys):
            addData(
                name,
                sheet.iloc[i, 1],
                data
            )

        return data

    def getVessels(self, sheet, enzmldoc):

        sheet = sheet.iloc[0:20, 0:4].applymap(self.__cleanSpaces)
        sheet = sheet.dropna(thresh=sheet.shape[-1]-1)

        # Vessel(name, id_, size, unit)
        # rename columns to match kwargs

        sheet.columns = ["id_", "name", "size", "unit"]
        sheet = sheet.set_index("id_")
        data = sheet.to_dict("index")

        enzmldoc.setVessel(
            Vessel(
                id_="v0",
                **data["v0"]
            )
        )

    def getReactants(self, sheet, enzmldoc):

        # Clean sheet
        sheet = sheet.iloc[0:20, 0:6].applymap(self.__cleanSpaces)
        sheet = sheet.dropna(thresh=sheet.shape[-1]-1)
        sheet = sheet.replace(np.nan, '#NULL#', regex=True)

        # Reactant(name, compartment, init_conc=0.0, substanceunits='NAN',
        # constant=False, smiles=None, inchi=None)
        # rename columns to match kwargs
        sheet.columns = [
            "id_",
            "name",
            "compartment",
            "constant",
            "smiles",
            "inchi"
        ]
        sheet = sheet.set_index("id_")

        data = sheet.to_dict("index")

        # Create PyEnzyme object
        def boolCheck(val):
            return bool(val) if val in "Not constant Constant" else val

        for id_, item in data.items():
            item = {
                key: boolCheck(val)
                for key, val in item.items()
                if val != '#NULL#'
            }
            item["compartment"] = enzmldoc.getVessel().getId()

            reactant = Reactant(**item)

            reac_id = enzmldoc.addReactant(reactant, custom_id=id_)
            self.reactantDict[reac_id] = reactant.getName()

    def getProteins(self, sheet, enzmldoc):

        # Clean sheet
        sheet = sheet.iloc[0:20, 0:8].applymap(self.__cleanSpaces)
        sheet = sheet.dropna(thresh=sheet.shape[-1]-3)

        sheet = sheet.replace(np.nan, '#NULL#', regex=True)

        # Protein(name, sequence, compartment=None, init_conc=None,
        # substanceunits=None, constant=True, ecnumber=None, uniprotid=None,
        # organism=None)
        # rename columns to match kwargs
        sheet.columns = [
            "id_",
            "name",
            "sequence",
            "compartment",
            "constant",
            "organism",
            "ecnumber",
            "uniprotid"
        ]
        sheet = sheet.set_index("id_")

        data = sheet.to_dict("index")

        # Create PyEnzyme object
        def boolCheck(val):
            return True if val == "Not constant" else False \
                    if val == "Constant" else val

        for id_, item in data.items():
            item = {
                key: boolCheck(val)
                for key, val in item.items()
                if val != '#NULL#'
            }
            item["compartment"] = enzmldoc.getVessel().getId()

            protein = Protein(**item)

            prot_id = enzmldoc.addProtein(
                protein,
                use_parser=False,
                custom_id=id_
            )
            self.proteinDict[prot_id] = protein.getName()

    # functions to extract elements
    def getReacElements(self, item):

        elements = {
                    "educts": item["educts"].split(', '),
                    "products": item["products"].split(', '),
                    "modifiers": item["modifiers"].split(', ') +
                    item["proteins"].split(', ')
                    }

        item.pop("educts")
        item.pop("products")
        item.pop("modifiers")
        item.pop("proteins")

        return item, elements

    def getReactions(self, sheet, enzmldoc):

        # Clean sheet
        sheet = sheet.iloc[0:20, 0:10].applymap(self.__cleanSpaces)
        sheet = sheet.dropna(thresh=sheet.shape[-1]-1)
        sheet = sheet.replace(np.nan, '#NULL#', regex=True)

        # EnzymeReaction(self, temperature, tempunit, ph, name, reversible,
        # educts=None, products=None, modifiers=None)
        # rename columns to match kwargs
        sheet.columns = [
            "id_",
            "name",
            "temperature",
            "tempunit",
            "ph",
            "reversible",
            "educts",
            "products",
            "proteins",
            "modifiers"
        ]
        sheet = sheet.set_index("id_")

        data = sheet.to_dict("index")

        # Create PyEnzyme object
        def boolCheck(val):
            return True if val == "reversible" else \
                    False if val == "irreversible" else val

        # rearrange unison of protein/reactantDict to guarantee consistency
        inv_prDict = {
            name: id_ for id_, name in {
                **self.proteinDict,
                **self.reactantDict}.items()
            }

        for id_, item in data.items():
            item, elements = self.getReacElements(item)
            item = {
                key: boolCheck(val)
                for key, val in item.items()
                if val != '#NULL#'
            }

            reac = EnzymeReaction(**item)

            # add elements
            elemMap = {
                "educts": reac.addEduct,
                "products": reac.addProduct,
                "modifiers": reac.addModifier
            }

            for key in elements:
                fun = elemMap[key]
                for elem in elements[key]:

                    if elem != "#NULL#":
                        elem_id = inv_prDict[elem]

                        if 's' in elem_id:
                            fun(
                                id_=elem_id,
                                stoichiometry=1.0,
                                constant=True,
                                enzmldoc=enzmldoc
                            )

                        elif 'p' in elem_id:
                            fun(
                                id_=elem_id,
                                stoichiometry=1.0,
                                constant=True,
                                enzmldoc=enzmldoc
                            )

                        else:
                            raise KeyError(
                                f"The identifier {elem_id} could not be parsed. \
                                Make sure the ID is either s for reactants \
                                or p for proteins."
                            )

            enzmldoc.addReaction(reac)

    def getData(self, sheet, enzmldoc):

        # Clean sheet
        sheet = sheet.dropna(how="all")
        sheet = sheet.replace(np.nan, '#NULL#', regex=True)

        reactions = set(sheet.iloc[:, 2])

        for reac in reactions:

            df_reac = sheet[sheet.iloc[:, 2] == reac]
            exp_ids = set(sheet.iloc[:, 0])

            for exp in exp_ids:

                # fetch individiual experiments
                df_exp = df_reac[df_reac.iloc[:, 0] == exp]
                exp_dict = dict(reactants=list())

                for index, row in df_exp.iterrows():

                    datType = row.iloc[1]

                    if "Time" in datType:

                        time_raw = [
                            val for val in list(row.iloc[9::])
                            if type(val) == float
                        ]

                        exp_dict["time"] = {
                            "unit": datType.split("[")[-1].split(']')[0],
                            "raw": [
                                val for val in time_raw if type(val) == float
                                ]
                        }

                    elif "Concentration" in datType or "Absorption" in datType:

                        if "Concentration" in datType:
                            data_type = "conc"
                        if "Absorption" in datType:
                            data_type = "abs"

                        data_raw = [
                            val for val in list(row.iloc[9::])
                            if type(val) == float
                        ]

                        reactant = enzmldoc.getReactant(
                            row.iloc[6],
                            by_id=False
                        ).getId()

                        init_val = row.iloc[7]
                        init_unit = repl_unit = row.iloc[8]

                        protein_id = enzmldoc.getProtein(
                            row.iloc[3],
                            by_id=False
                        ).getId()

                        protein_init_val = row.iloc[4]
                        protein_init_unit = row.iloc[5]

                        enzmldoc.getReactant(reactant).setInitConc(init_val)
                        enzmldoc.getReactant(reactant).setSubstanceUnits(
                            UnitCreator().getUnit(init_unit, enzmldoc)
                        )

                        if data_type == "abs":
                            repl_unit = "abs"

                        if len(data_raw) > 0:

                            exp_dict["reactants"] += [{
                                "id": reactant,
                                "unit": repl_unit,
                                "init_val": init_val,
                                "raw": data_raw,
                                "type": data_type
                            }]

                            # Add Protein initial concentration to modifier
                            enzmldoc.getReaction(
                                reac, by_id=False
                                ).addInitConc(
                                        protein_id,
                                        protein_init_val,
                                        protein_init_unit,
                                        enzmldoc
                            )

                            enzmldoc.getProtein(
                                protein_id
                                ).setInitConc(
                                    protein_init_val
                            )

                            enzmldoc.getProtein(
                                protein_id
                                ).setSubstanceUnits(
                                        UnitCreator().getUnit(
                                            protein_init_unit, enzmldoc
                                        )
                            )

                        else:
                            # Add initial concentration although
                            # no raw data is given
                            enzmldoc.getReaction(
                                reac, by_id=False
                                ).addInitConc(
                                    reactant,
                                    init_val,
                                    init_unit,
                                    enzmldoc
                            )

                            # Add Protein initial concentration to modifier
                            enzmldoc.getReaction(
                                reac,
                                by_id=False).addInitConc(
                                    protein_id,
                                    protein_init_val,
                                    protein_init_unit,
                                    enzmldoc
                            )

                            enzmldoc.getProtein(
                                protein_id
                                ).setInitConc(
                                    protein_init_val
                            )

                            enzmldoc.getProtein(
                                protein_id
                                ).setSubstanceUnits(
                                    UnitCreator().getUnit(
                                        protein_init_unit,
                                        enzmldoc)
                            )

                # add replicates to enzmldoc
                for i, reactant in enumerate(exp_dict["reactants"]):

                    repl = Replicate(
                        replica=f"repl_{exp}_{i}",
                        reactant=reactant["id"],
                        type_=reactant["type"],
                        data_unit=reactant["unit"],
                        time_unit=exp_dict["time"]["unit"],
                        init_conc=reactant["init_val"],
                        data=reactant["raw"],
                        time=exp_dict["time"]["raw"]
                    )

                    enzmldoc.getReaction(
                        reac,
                        by_id=False
                        ).addReplicate(
                            repl,
                            enzmldoc
                    )
