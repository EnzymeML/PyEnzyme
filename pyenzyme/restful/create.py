'''
File: create.py
Project: restful
Author: Jan Range
License: BSD-2 clause
-----
Last Modified: Wednesday June 23rd 2021 7:44:37 pm
Modified By: Jan Range (<jan.range@simtech.uni-stuttgart.de>)
-----
Copyright (c) 2021 Institute of Biochemistry and Technical Biochemistry Stuttgart
'''

from flask import request, send_file
from flask_apispec import doc, marshal_with, MethodResource

import tempfile
import os
import shutil
import io

from pyenzyme.enzymeml.core import EnzymeMLDocument, Protein, Reactant, EnzymeReaction, Replicate, Vessel, Creator
from pyenzyme.enzymeml.models import KineticModel
from pyenzyme.restful.create_schema import EnzymeMLSchema

desc = 'This endpoint is used to create an EnzymeML Document from a JSON representation. \
        The endpoint will return your data as an EnzymeML OMEX file.'


class Create(MethodResource):

    @doc(tags=['Create EnzymeML'], description=desc)
    @marshal_with(EnzymeMLSchema(), code=200)
    def post(self):
        """
        Reads JSON formatted data and converts to an EnzymeML container.
        """

        json_data = request.get_json(force=True)

        # create enzymeml document
        param_doc = {
            key: item for key, item in json_data.items()
            if type(item) != list and type(item) != dict
        }
        enzmldoc = EnzymeMLDocument(**param_doc)

        # create Creator
        creators = [Creator(**creator) for creator in json_data['creator']]
        enzmldoc.setCreator(creators)

        # create vessel
        vessel = Vessel(**json_data["vessel"][0])
        enzmldoc.setVessel(vessel)

        # parse proteins
        for protein in json_data['protein']:
            enzmldoc.addProtein(
                Protein(**protein)
            )

        # parse reactants
        for reactant in json_data['reactant']:
            enzmldoc.addReactant(
                Reactant(**reactant)
            )

        # parse reactions
        for reaction in json_data['reaction']:
            # initialize reaction meta data
            param_reac = {
                key: item for key, item in reaction.items()
                if type(item) != list and type(item) != dict
            }

            reac = EnzymeReaction(**param_reac)

            # add educts by name
            for educt in reaction['educts']:
                self.parseReacElements(
                    reac.addEduct,
                    educt,
                    reac,
                    enzmldoc
                )

            # add products by name
            for product in reaction['products']:
                self.parseReacElements(
                    reac.addProduct,
                    product,
                    reac,
                    enzmldoc
                )

            # add modifiers by name
            for modifier in reaction['modifiers']:
                self.parseReacElements(
                    reac.addModifier,
                    modifier,
                    reac,
                    enzmldoc
                )

            if 'kineticmodel' in reaction.keys():

                # kinetic models
                model = reaction['kineticmodel']
                equation = model['equation']
                parameters = dict()

                for parameter in model['parameters']:

                    name = parameter['name']
                    reactant = enzmldoc.getReactant(
                        parameter['reactant'],
                        by_id=False
                        ).getId()
                    value = parameter['value']
                    unit = parameter['unit']

                    parameters[f"{name}_{reactant}"] = (value, unit)

                km = KineticModel(equation, parameters)
                reac.setModel(km)

            enzmldoc.addReaction(reac)

        # Send File
        dirpath = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "create_temp"
        )
        os.makedirs(dirpath, exist_ok=True)
        dirpath = os.path.join(
            dirpath,
            next(tempfile._get_candidate_names())
        )

        enzmldoc.toFile(dirpath)

        path = os.path.join(
                            dirpath,
                            enzmldoc.getName() + '.omex'
                            )

        f = io.BytesIO(open(path, "rb").read())
        f.name = enzmldoc.getName() + '.omex'

        shutil.rmtree(dirpath, ignore_errors=True)

        return send_file(
            f,
            mimetype='omex',
            as_attachment=True,
            attachment_filename='%s.omex' % enzmldoc.getName()
        )

    def parseReacElements(self, func, body, reac, enzmldoc):
        """
        Parses Reaction elements based on given function func. Internal usage!

        Args:
            func (addXXX Function): EnzymeReaction function to add Educt/Product/Modifier
            body (Dictionaly): JSON body describing list of educts/products/modifiers
            reac (EnzymeReaction): Object used to add respective Entities as well as Replicates
            enzmldoc (EnzymeMLDocument): Used for consistency and name parsing

        Raises:
            KeyError: Raises error if given reactants/proteins are not given
        """

        try:
            # Check if it is a reactant
            species_id = enzmldoc.getReactant(
                body['species'],
                by_id=False
            ).getId()

        except KeyError:
            try:
                # Check if it is a protein
                species_id = enzmldoc.getProtein(
                    body['species'],
                    by_id=False
                ).getId()

            except KeyError:
                raise KeyError(
                    f"Reactant/Protein {body['species']} not found in body! \
                    Make sure entries are consistent")

        func(
            species_id,
            body['stoich'],
            body['constant'],
            enzmldoc
            )

        for repl in body['replicates']:

            replicate = Replicate(**repl)
            replicate.setReactant(species_id)
            reac.addReplicate(replicate, enzmldoc)
