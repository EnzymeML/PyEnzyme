"""
File: TL_Pysces.py
Project: ThinLayers
Author: Johann Rohwer (j.m.rohwer@gmail.com)
License: BSD-2 clause
-----
Copyright (c) 2021 Stellenbosch University
"""

from pyenzyme.enzymeml.core import EnzymeMLDocument
import numpy as np
import pandas as pd
import os
import pysces
import libcombine
import lmfit


class ThinLayerPysces():

    def __init__(self, omexarchive):
        self.omexarchive = omexarchive
        self.enzmldoc = EnzymeMLDocument.fromFile(omexarchive)
        self.mod = self._getPyscesModel(omexarchive)

    def _getPyscesModel(self, omexarchive):
        if not os.path.isdir('pysces'):
            os.mkdir('pysces')
        a = libcombine.CombineArchive()
        a.initializeFromArchive(omexarchive)
        sbmlfilename = os.path.split(a.getEntry(0).getLocation())[1]
        if not (
            os.path.isfile(f'./pysces/{sbmlfilename}')
            and os.path.isfile(f'./pysces/{sbmlfilename}.psc')
            and (
                os.path.getmtime(f'./pysces/{sbmlfilename}.psc')
                > os.path.getmtime(f'./pysces/{sbmlfilename}')
            )
        ):
            a.extractEntry(sbmlfilename, './pysces')
            pysces.interface.convertSBML2PSC(
                sbmlfilename, sbmldir='./pysces', pscdir='./pysces'
            )
        return pysces.model(sbmlfilename, dir='./pysces')

    def _getExperimentalData(self):

        measurements = []
        inits = []

        for m in self.enzmldoc.measurement_dict.values():

            # ? It is now possible to ensure, that the units are the same: m.unifyUnits(kind="mole", scale=-3)
            measurement_data = m.exportData()
            replicate_df = measurement_data['reactants']['data']
            # rename_dict = {i: i.split('/')[-2] for i in replicate_df.columns}
            # replicate_df.rename(rename_dict, axis=1, inplace=True)

            inits_dict = {}

            for reactant_id, (init_value, _) in measurement_data['reactants']['initConc'].items():
                inits_dict[reactant_id] = init_value

            for protein_id, (init_value, _) in measurement_data['proteins']['initConc'].items():
                inits_dict[protein_id] = init_value

            inits_dict['time'] = replicate_df.time
            inits.append(inits_dict)

            measurements.append(replicate_df.drop('time', axis=1))

        expdata = pd.concat(measurements)
        expdata.reset_index(inplace=True)
        expdata.drop('index', axis=1, inplace=True)

        self.expdata = expdata
        self.inits = inits
        return expdata, inits

    def _simulateExpData(self, params):
        self.mod.SetQuiet()
        parvals = params.valuesdict()
        for p, v in parvals.items():
            setattr(self.mod, p, v)
        output = []
        for i in self.inits:
            for k, v in i.items():
                if (type(v) == int or type(v) == float) and v == 0.0:
                    v = 1.0e-6
                if k in self.mod.species:
                    setattr(self.mod, f"{k}_init", v)
                elif k == "time":
                    self.mod.sim_time = np.array(v)
                else:
                    setattr(self.mod, k, v)
            self.mod.Simulate(userinit=1)
            output.append([getattr(self.mod.sim, s) for s in self.mod.species])
        return pd.DataFrame(np.hstack(output).T, columns=self.mod.species)

    def _residual(self, params):
        exp_data, inits = self._getExperimentalData()
        # get columns of experimental data, corresponding to measured reactants
        cols = list(exp_data.columns)
        model_data = self._simulateExpData(params)
        # create dataframe containing only modelled data for reactants that have also been measured
        new_model_data = model_data.drop(
            model_data.columns.difference(cols), axis=1)
        return np.array(exp_data - new_model_data)

    def _getParamsFromEnzymeML(self):
        params = {}
        for rID, r in self.enzmldoc.reaction_dict.items():
            for kinetic_parameter in r.model.parameters:
                params[f"{rID}_{kinetic_parameter.name}"] = kinetic_parameter.value
        return params

    def _makeLmfitParameters(self):
        modelparams = self._getParamsFromEnzymeML()
        params = lmfit.Parameters()
        for k, v in modelparams.items():
            params.add(k, v, vary=True, min=1.0e-9)
        return params

    def runOptimisation(self, params=None):
        if params is None:
            params = self._makeLmfitParameters()
        self.mini = lmfit.Minimizer(self._residual, params)
        return self.mini.minimize()
