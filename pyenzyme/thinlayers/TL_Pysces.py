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
        for m in self.enzmldoc.getMeasurementDict().values():
            mdata = m.exportData()
            repdata = mdata['reactants']['data']
            renamedict = {i: i.split('/')[-2] for i in repdata.columns}
            repdata.rename(renamedict, axis=1, inplace=True)
            initsdict = {}
            for k, v in mdata['reactants']['initConc'].items():
                initsdict[k] = v[0]
            for k, v in mdata['proteins']['initConc'].items():
                initsdict[k] = v[0]
            initsdict['time'] = repdata.time
            inits.append(initsdict)
            measurements.append(repdata.drop('time', axis=1))
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
        model_data = self._simulateExpData(params)
        return np.array(exp_data - model_data)

    def _getParamsFromEnzymeML(self):
        params = {}
        for rID, r in self.enzmldoc.getReactionDict().items():
            for pname, pval in r.getModel().getParameters().items():
                params[f"{rID}_{pname}"] = pval[0]
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
        self.fit = self.mini.minimize()
        return self.fit

    def _addResultsToEnzymeML(self):
        '''
        Add fit results to EnzymeML document.
        '''
        for name, value in self.fit.params.valuesdict().items():
            reaction_id = name.split('_')[0]
            parameter_name = "_".join(name.split('_')[1:])
            parameters = self.enzmldoc.getReaction(reaction_id).getModel().getParameters()
            (value_old, unit) = parameters[parameter_name]
            parameters[parameter_name] = (value, unit)

    def writeEnzymeML(self, name=None):
        '''
        Write EnzymeML document with fit results.
        WARNING: will overwrite old EnzymeML document if no new name is provided.

        Args:
            name (str): new name for EnzymeML document
        '''
        if name is not None:
            self.enzmldoc.setName(name)
        self._addResultsToEnzymeML()
        self.enzmldoc.toFile('.')
