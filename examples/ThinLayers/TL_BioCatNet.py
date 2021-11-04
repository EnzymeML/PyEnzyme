'''
File: TL_BioCatNet.py
Project: ThinLayers
Author: Jan Range
License: BSD-2 clause
-----
Last Modified: Wednesday June 23rd 2021 9:45:29 pm
Modified By: Jan Range (<jan.range@simtech.uni-stuttgart.de>)
-----
Copyright (c) 2021 Institute of Biochemistry and Technical Biochemistry Stuttgart
'''

import pandas as pd
import numpy as np
import re
import os
from pyenzyme.enzymeml.core.enzymemldocument import EnzymeMLDocument
from pyenzyme.enzymeml.core.vessel import Vessel
from pyenzyme.enzymeml.core.reactant import Reactant
from pyenzyme.enzymeml.core.protein import Protein
from pyenzyme.enzymeml.core.enzymereaction import EnzymeReaction
from pyenzyme.enzymeml.core.replicate import Replicate
from pyenzyme.enzymeml.tools.enzymemlwriter import EnzymeMLWriter
from copy import deepcopy


class ThinlayerBioCatNet():

    def toEnzymeML(self, path, out=None):

        # set path for loading
        self.path = os.path.normpath(path)
        if out:
            out = os.path.normpath(out)
        else:
            out = os.path.dirname(self.path)

        self.__parseXLSX()

        # initialize EnzymeMLDocument
        enzmldoc = EnzymeMLDocument(self.exp)

        # set vessel
        vessel = Vessel("Vessel", "v0", self.vessel['vessel_val'], self.vessel['vessel_unit'])
        enzmldoc.setVessel(vessel)

        # set proteins
        for key, protein in self.proteins.items():
            protein = Protein(key, protein['sequence'], "v0", protein['conc_val'], protein['conc_unit'])
            enzmldoc.addProtein(protein)

        # set buffer
        buffer = Reactant(self.buffer['name'], "v0", self.buffer['conc_val'], self.buffer['conc_unit'], constant=True)
        enzmldoc.addReactant(buffer)

        # set reactants
        for key, reac in self.reactants.items():
            reactant = Reactant(key, "v0", reac['conc_val'], reac['conc_unit'], constant=False)
            reactant.setSmiles(reac['smiles'])
            enzmldoc.addReactant(reactant)

        for key, reac in self.reactions.items():
            
            # set reaction
            enzymereac = EnzymeReaction( reac['temp'], "C", reac['ph'] , reac['name'] + "_%i" % key, reversible=True)

            # add educts
            educts = reac['educts']
            for stoich, educt in educts:
                enzymereac.addEduct( enzmldoc.getReactant( educt , by_id=False).getId() , stoich, False, enzmldoc)

            # add educts
            products = reac['products']
            for stoich, product in products:
                enzymereac.addProduct( enzmldoc.getReactant( product , by_id=False).getId() , stoich, False, enzmldoc)

            # add modifier and protein to reaction
            enzymereac.addModifier( "s0" , 1.0, True, enzmldoc)
            enzymereac.addModifier( enzmldoc.getProtein( self.measurements[key][0], by_id=False).getId() , 1.0, True, enzmldoc )

            # add replicates
            for repl in reac['replicates']:

                data = repl['data']
                data.index.names = [ "time/%s" % repl['time_unit'] ]
                data = data.rename( "%s/%s/conc" % ( repl['id'], enzmldoc.getReactant( repl['reactant'], by_id=False).getId() ) )
                
                replicate = Replicate(
                    replica=repl['id'],
                    reactant=enzmldoc.getReactant(repl['reactant'], by_id=False).getId(),
                    type_="conc",
                    data_unit=repl['data_unit'],
                    time_unit=repl['time_unit'],
                    init_conc=enzmldoc.getReactant(repl['reactant'], by_id=False).getInitConc(),
                    measurement=repl['measurementID']
                                       )

                replicate.setData(data)
                enzymereac.addReplicate(replicate, enzmldoc)

            enzmldoc.addReaction(enzymereac)
            del enzymereac

        reactions = self.__collapseEnzymeML(enzmldoc)
        self.__finalizeEnzymeML(enzmldoc, reactions)

        writer = EnzymeMLWriter()
        writer.toFile(enzmldoc, out)

    def __finalizeEnzymeML(self, enzmldoc, reactions):

        ref = deepcopy(enzmldoc)

        enzmldoc.setProteinDict(dict())
        enzmldoc.setReactantDict(dict())
        enzmldoc.setReactionDict(dict())

        for i, reaction in enumerate(reactions):

            educts = reaction['educts']
            products = reaction['products']
            modifiers = reaction['modifiers']

            reac_obj = reaction['reaction']
            reac_obj.setName( reac_obj.getName() + '_%i' % i )

            # add new species
            for key, tup in educts.items():
                
                reactant = deepcopy(ref.getReactant( tup[0] ))
                reactant.setName( key )
                reactant_id = enzmldoc.addReactant(reactant, use_parser=False)

                reps = []

                for index, rep in enumerate(tup[3]):
                    rep = deepcopy( rep )
                    rep.setReactant( reactant_id )
                    rep.setReplica(
                        'repl_' +
                        rep.getMeasurement() + '_' +
                        str(index)
                    )
                    reps.append( rep )

                reac_obj.addEduct(
                    speciesID=reactant_id,
                    stoichiometry=tup[1],
                    isConstant=tup[2],
                    enzmldoc=enzmldoc,
                    replicates=reps,
                    initConcs=tup[4]
                    )

            for key, tup in products.items():
                reactant = deepcopy(ref.getReactant( tup[0] ))
                reactant.setName( key )
                reactant_id = enzmldoc.addReactant(reactant, use_parser=False)

                reps = []

                for index, rep in enumerate(tup[3]):
                    rep = deepcopy( rep )
                    rep.setReactant( reactant_id )
                    rep.setReplica(
                        'repl_' +
                        rep.getMeasurement() + '_' +
                        str(index)
                    )
                    reps.append( rep )

                reac_obj.addProduct(
                    speciesID=reactant_id,
                    stoichiometry=tup[1],
                    isConstant=tup[2],
                    enzmldoc=enzmldoc,
                    replicates=reps,
                    initConcs=tup[4]
                    )

            for key, tup in modifiers.items():

                if 's' in tup[0]: reactant = deepcopy(ref.getReactant( tup[0] ));
                if 'p' in tup[0]: reactant = deepcopy(ref.getProtein( tup[0] ));
                if 's' in tup[0]: reactant_id = enzmldoc.addReactant(reactant, use_parser=False)
                if 'p' in tup[0]: reactant_id = enzmldoc.addProtein(reactant, use_parser=False)
                reactant.setName( key )
                reac_obj.addModifier(
                    speciesID=reactant_id,
                    stoichiometry=tup[1],
                    isConstant=tup[2],
                    enzmldoc=enzmldoc,
                    replicates=tup[3],
                    initConcs=tup[4]
                    )

            enzmldoc.addReaction( reac_obj )

    def __collapseEnzymeML(self, enzmldoc):

        # reduce proteins to a unique set
        prot_set = dict()
        prot_ref = dict()

        for reac in enzmldoc.getReactionDict().values():

            prot_id = reac.getModifiers()[-1][0]
            prot_conc = enzmldoc.getProtein(prot_id).getInitConc()

            if prot_conc not in prot_set.values():
                prot_set[prot_id] = prot_conc
                prot_ref[prot_id] = [prot_id]
            else:
                prot_ref[ [ id_ for id_, conc in prot_set.items() if conc == prot_conc ][0] ].append( prot_id )

        # collect initial concentrations and construct new reactions
        reactions = []
        for prot in prot_ref:

            educts = []
            modifiers = []
            products = []

            for key, reac in enzmldoc.getReactionDict().items():

                if reac.getModifiers()[-1][0] in prot_ref[prot]:

                    educts += reac.getEducts()
                    products += reac.getProducts()
                    mods = reac.getModifiers()
                    mods[-1] = ( mods[-1][0], mods[-1][1], mods[-1][2], mods[-1][3], mods[-1][4] )
                    modifiers += mods



            educt_dict = self.__sumElements(educts, enzmldoc)
            product_dict = self.__sumElements(products, enzmldoc)
            modifiers_dict= self.__sumElements(modifiers, enzmldoc)

            enz_reaction = EnzymeReaction(
                reac.getTemperature(),
                "C",
                reac.getPh(),
                reac.getName(),
                reac.getReversible()
                )

            reactions.append( { 'reaction': enz_reaction, 'educts': educt_dict, 'products': product_dict, 'modifiers': modifiers_dict } )

        return reactions

    def __sumElements(self, elements, enzmldoc):

        element_dict = {}

        for tup in elements:
            id_ = tup[0]
            if 's' in id_: name = enzmldoc.getReactant(id_).getName();
            if 'p' in id_: name = enzmldoc.getProtein(id_).getName();
            stoich = tup[1]
            const = tup[2]
            reps = tup[3]
            inits = tup[4]


            if name.split('_')[0] not in element_dict:
                if '_' in name and 's' in id_:
                    element_dict[ name.split('_')[0] ] = (
                        tup[0],
                        tup[1],
                        tup[2],
                        tup[3],
                        [(
                            enzmldoc.getReactant(id_).getInitConc(),
                            enzmldoc.getReactant(id_).getSubstanceUnits()
                            )
                        ]
                    )
                else:
                    element_dict[ name.split('_')[0] ] = tup
            else:
                if '_' in name:

                    if 's' in id_:

                        nu_reps = element_dict[ name.split('_')[0] ][3] + reps

                        for i, rep in enumerate(nu_reps):
                            nu_reps[i].setReactant( id_ )

                        element_dict[ name.split('_')[0] ] = (

                            id_,
                            stoich,
                            const,
                            nu_reps,
                            element_dict[ name.split('_')[0] ][4] + [(
                                enzmldoc.getReactant(id_).getInitConc(),
                                enzmldoc.getReactant(id_).getSubstanceUnits()
                            )]

                            )
                    elif 'p' in id_:

                        element_dict[ enzmldoc.getProtein( id_ ).getName().split('_')[0] ]  = (

                            id_,
                            1.0,
                            True,
                            [],
                            []
                            )


        return element_dict

    def __parseXLSX( self ):

        self.doc = pd.read_excel( self.path, sheet_name=["user information", "sequences", "conditions", "reaction", "measured compounds", "measured parameters" ] )
        self.ui = self.doc['user information']
        self.seqs = self.doc['sequences']
        self.conds = self.doc['conditions']
        self.reacs = self.doc['reaction']
        self.comps = self.doc['measured compounds']
        self.comps.columns=self.comps.iloc[0]
        self.comps = self.comps.drop( self.comps.index[0])
        self.params = self.doc['measured parameters']

        # initialize dicts
        self.proteins = dict()
        self.reactants = dict()
        self.measurements = dict()
        self.reactions = dict()
        self.meas_index = 1

        # parse user info
        self.__getUI()

        # parse vessel
        self.__getVessel()

        # parser proteins
        self.__getProteins()

        # parse reactants
        self.__getReactants()
        self.__getBuffer()

        # parse reaction and replicates
        self.__getReaction()

    def __getReaction( self ):

        name = self.__filter( self.reacs, "reaction type", x=-2, y =1 )['reaction type_0']
        reac_string = self.__filter( self.reacs, "reaction type", x=-1, y =1 )["reaction type_0"].replace('', '')
        educts = [ self.__getStoich(string) for string in reac_string.split('->')[0].split('+') ]
        products = [ self.__getStoich(string) for string in reac_string.split('->')[1].split('+') ]

        replicateIndex = 0
        
        for key, item in self.measurements.items():

            # replace elements with proper indexed measurement elements
            meas_educts = deepcopy(educts)
            for educt in item:
                for i, tup in enumerate(meas_educts):

                    if educt.split('_')[0] == tup[-1]:
                        meas_educts[i] = (tup[0], educt)

            meas_products = deepcopy(products)

            for product in item:
                for i, tup in enumerate(meas_products):

                    if product.split('_')[0] == tup[-1]:
                        meas_products[i] = (tup[0], product)


            self.reactions[key] = {

                'name': name,
                'ph': self.__filter( self.conds, "pH ", y=1 )["pH _0"],
                'temp': float(self.__filter( self.conds, "pH ", x=-1, y=1 )["pH _0"]),
                'educts': meas_educts ,
                'products': meas_products,
                'modifiers': self.buffer

            }

            # get appropiate replicates
            df_meas = self.comps[ self.comps["MEASUREMENT NO."] == key ]

            # get numbers of replicates
            repls = list(set( df_meas['replication no.'] ))
            replicates = []
            for repl in repls:

                df_repl = df_meas[ df_meas['replication no.'] == repl ]
                reac = list(set( df_meas['COMPOUND NAME'] ))[0] + "_%s" % str(key)
                time = df_repl["TIME VALUE"].tolist()
                time_unit = list(set(df_repl["TIME UNIT"]))[0]
                data = df_repl["CONCENTRATION VALUE"]
                data.index = time
                data_unit = list(set(df_repl["CONCENTRATION UNIT"]))[0].replace('mol', 'mole')                

                replicates.append( {
                                        "reactant": reac,
                                        "id": "repl_%i" % replicateIndex,
                                        "time_unit": time_unit,
                                        "data": data,
                                        "data_unit":data_unit,
                                        "measurementID": f"m{key}"
                                    } )

                replicateIndex += 1
                
            self.reactions[key]['replicates'] = replicates

    def __getProteins( self ):

        # Parse sequence from sheet
        i = 1
        while True:

            row = self.seqs.iloc[i]

            if str(row[0]) == "nan":
                break
            else:
                self.proteins[ row[0] ] = {'sequence': row[2]}
                i += 1

        # Get Concentration values
        name = list(self.proteins.keys())[0]
        conc_val = self.__filter( self.reacs, name, x=3 )
        conc_unit = self.__filter( self.reacs, name, x=4 )
        meas_num = self.__filter( self.reacs, name, x=-1 )

        prot_meta = { key.split('_')[0] + "_%i" % meas_num[key] : ( conc_val[key], conc_unit[key], meas_num[key] ) for key in conc_val }

        # get all measurements
        for i, prot in enumerate(prot_meta):

            self.measurements[prot_meta[prot][2]] = [ prot ]

            self.proteins[prot] = dict()
            self.proteins[prot]['sequence'] = self.proteins[name]['sequence']
            self.proteins[prot]['conc_val'] = float( prot_meta[prot][0] )
            self.proteins[prot]['conc_unit'] = prot_meta[prot][1].replace('mol', 'mole')

        self.proteins.pop(name)

    def __getReactants( self ):

        # parse all compounds including their
        i = 1
        while True:
            row = self.reacs.iloc[i]
            name = row[0]

            if str(name) == "nan" or name == "REACTION":
                break
            else:

                smiles = self.__filter(self.reacs, name, x=1)["%s_0" % name]
                conc_val = self.__filter(self.reacs, name, x=3)
                conc_unit = self.__filter(self.reacs, name, x=4)
                meas_num = self.__filter( self.reacs, name, x=-1 )

                reac_meta = { key.split("_")[0] + "_%i" % (int(meas_num[key])): ( conc_val[key], conc_unit[key], meas_num[key] ) for key in conc_val if key.split('_')[-1] != "0" }

                if len(reac_meta.keys()) > 0:

                    for reac in reac_meta:
                        self.measurements[ reac_meta[reac][-1] ].append(reac)
                        self.reactants[ reac ] = dict()
                        self.reactants[ reac ]['smiles'] = smiles
                        self.reactants[ reac ]["conc_val"] = float( reac_meta[reac][0] )
                        self.reactants[ reac ]["conc_unit"] = reac_meta[reac][1].replace('mol', 'mole')

                else:

                    self.reactants[ name ] = dict()
                    self.reactants[ name ]["conc_val"] = 0.0
                    self.reactants[ name ]["smiles"] = smiles
                    self.reactants[ name ]["conc_unit"] = "NAN"

                i += 1


    def __getBuffer( self ):

        name = self.__filter(self.conds, "BUFFER", y=2)['BUFFER_0']
        conc_val = float( self.__filter(self.conds, "CONCENTRATION VALUE", y=1)[ "CONCENTRATION VALUE_0" ] )
        conc_unit = self.__filter(self.conds, "CONCENTRATION UNIT", y=1)[ "CONCENTRATION UNIT_0" ].replace('mol', 'mole')

        self.buffer = {
            'name': name,
            'conc_val': conc_val,
            'conc_unit': conc_unit
        }

    def __getVessel( self ):

        vessel_val = float( self.__filter(self.conds, "initial  volume value", y=1)["initial  volume value_0"] )
        vessel_unit = self.__filter(self.conds, "initial  volume value", y=1, x=1)["initial  volume value_0"].replace('mol', 'mole')

        self.vessel = { "vessel_val": vessel_val, 'vessel_unit': vessel_unit }


    def __getUI( self ):

        vals = self.__filter( self.ui, ["NAME", "EMAIL"], y=1 )
        self.user = vals['NAME_0']
        self.exp = vals['NAME_1']
        self.mail = vals["EMAIL_0"]

    def __getCoords( self, df, cond ):
        return [(x, y) for x, y in zip(*np.where(df.values == cond))]

    def __filter( self, df, conds, y=0, x=0 ):
        results = dict()

        if type(conds) == str:
            conds = [conds]

        for cond in conds:
            coords = self.__getCoords( df, cond )

            for i, coord in enumerate(coords):
                results[ cond + "_" + str(i) ] = df.iloc[ coord[0]+y, coord[1]+x ]

        return results

    def __getStoich(self, string):

        regex = "[\s]?([\d]?)[xX\s]?([\D a-zA-z\s\d0-9_-]*)[/s]?$"
        reg = re.compile(regex)
        res = reg.findall(string)[0]

        if res[1][-1] == " ":
            res = list(res)
            res[1] = res[1][0:-1]
            res = tuple(res)

        if len(res[0]) == 0:
            return ( 1.0, res[1])
        else:
            return ( float(res[0]), res[1] )

    def __getReplicates(self):

        replicates = []

        for reac in self.reactants:

            df_reac = self.comps[ self.comps["COMPOUND NAME"] == reac ]

            if df_reac.shape[0] > 0:

                # get numbers of replicates
                repls = list(set( df_reac['replication no.'] ))

                for repl in repls:

                    df_repl = df_reac[ df_reac['replication no.'] == repl ]

                    time = df_repl["TIME VALUE"]
                    time_unit = list(set(df_repl["TIME UNIT"]))[0]
                    data = df_repl["CONCENTRATION VALUE"]
                    data.index = time
                    data_unit = list(set(df_repl["CONCENTRATION UNIT"]))[0].replace('mol', 'mole')

                    replicates.append( {
                                            "reactant": reac,
                                            "id": "repl%i" % (len(replicates)),
                                            "time_unit": time_unit,
                                            "data": data,
                                            "data_unit":data_unit
                                        } )

            self.reaction["replicates"] = replicates

if __name__ == '__main__':
    path = os.path.join( 'BioCatNet', 'DMBA_selfligation.xlsx' )
    ThinlayerBioCatNet().toEnzymeML(path)
