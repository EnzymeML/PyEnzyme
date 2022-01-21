'''
File: TL_Copasi.py
Project: ThinLayers
Author: Jan Range
Author: Frank Bergmann
License: BSD-2 clause
-----
Last Modified: Wednesday June 23rd 2021 10:25:11 pm
Modified By: Jan Range (<jan.range@simtech.uni-stuttgart.de>)
-----
Copyright (c) 2021 Institute of Biochemistry and Technical Biochemistry Stuttgart
'''
import logging
from typing import Union

from pyenzyme.thinlayers import BaseThinLayer
import os

import COPASI
import pandas as pd
from builtins import enumerate


class ThinLayerCopasi(BaseThinLayer):

    def __init__(self, path, outdir, measurement_ids: Union[str, list] = "all"):
        """
        Initializes a new instance of the COPASI thin layer, by loading the EnzymeML file
        specified in `path` and creating a COPASI file (+ data) in `outdir`.

        :param path: the enzyme ml document to load
        :param outdir: the output dir
        :param measurement_ids: the measurement ids or all
        """

        # initialize base class, let it do the reading
        BaseThinLayer.__init__(self, path, measurement_ids)
        self.name = self.enzmldoc.name
        self.working_dir = os.path.join(os.path.abspath(outdir), self.name)
        self.cps_file = os.path.join(self.working_dir, self.name + '.cps')
        if not os.path.exists(self.working_dir):
            os.makedirs(self.working_dir)

        # now initialize the COPASI document from it
        self.dm = COPASI.CRootContainer.addDatamodel()
        try:
            self.dm.importSBMLFromString(self.sbml_xml)
        except COPASI.CCopasiException:
            logging.error(COPASI.CCopasiMessage.getAllMessageText())

        # maps
        self._init_maps()

        # variables
        self.model = self.dm.getModel()
        self.task = self.dm.getTask('Parameter Estimation')
        self.task.setScheduled(True)
        self.task.setUpdateModel(True)
        self.task.setMethodType(COPASI.CTaskEnum.Method_HookeJeeves)
        self.problem = self.task.getProblem()
        self.problem.setCalculateStatistics(False)
        self.exp_set = self.problem.getExperimentSet()

        # read in experiments
        self._import_experiments()

        # set all parameters as fit items
        self._set_default_items()

        self.dm.saveModel(self.cps_file, True)

    def _init_maps(self):
        """Initializes a map from SBML id to COPASI objects"""
        self.sbml_id_map = {}
        for item in self.dm.getModel().getMetabolites():
            self.sbml_id_map[item.getSBMLId()] = item
        for item in self.dm.getModel().getModelValues():
            self.sbml_id_map[item.getSBMLId()] = item
        for item in self.dm.getModel().getReactions():
            self.sbml_id_map[item.getSBMLId()] = item
        for item in self.dm.getModel().getCompartments():
            self.sbml_id_map[item.getSBMLId()] = item

    def _get_cn_for_item(self, item):
        """Resolves the given item to CN or None

        :param item: dictionary with 'name' and optinally 'reaction_id'
        :type item: dict
        :return: the CN if found, or None
        :rtype: COPASI.CCommonName
        """
        reaction = None
        if 'reaction_id' in item and item['reaction_id'] in self.sbml_id_map:
            reaction = self.sbml_id_map[item['reaction_id']]

        if 'name' in item:
            if reaction is not None:
                return reaction.getParameterObjects(item['name'])[0].getCN()

            mv = self.model.getModelValue(item['name'])
            if mv is not None:
                return mv.getInitialValueReference().getCN()

            metab = self.model.getMetabolite(item['name'])
            if metab is not None:
                return metab.getInitialConcentrationReference().getCN()

        return None

    def _import_experiments(self):
        """ Writes all experiments to TSV file and performs mapping in COPASI

        :return: None
        """
        for measurement_id, measurement_dict in self.data.items():
            sbml_ids = [d[0] if len(d) == 2 else d[1] for d in [
                c.split('|') for c in measurement_dict['data'].columns.to_list()
            ]]

            data = measurement_dict['data']

            for k, v in measurement_dict['initConc'].items():
                data = data.join(pd.DataFrame({'init_{0}'.format(k): [v[0]]}))
                sbml_ids.append('init_{0}'.format(k))

            exp_filename = os.path.abspath(os.path.join(self.working_dir, measurement_id + '.tsv'))

            data.to_csv(exp_filename,
                        sep='\t', header=True, index=False)

            exp = COPASI.CExperiment(self.dm)
            exp.setObjectName(
                '{0}'.format(measurement_id)
            )
            exp.setFirstRow(1)
            exp.setLastRow(data.shape[0] + 1)
            exp.setHeaderRow(1)
            exp.setFileName(exp_filename)
            exp.setExperimentType(COPASI.CTaskEnum.Task_timeCourse)
            exp.setSeparator('\t')
            exp.setNumColumns(len(sbml_ids))
            exp = self.exp_set.addExperiment(exp)
            info = COPASI.CExperimentFileInfo(self.exp_set)
            info.setFileName(exp_filename)

            # Mapping from .tsv file to COPASI bindings
            obj_map = exp.getObjectMap()
            obj_map.setNumCols(data.shape[1])

            for i, col in enumerate(sbml_ids):
                if col == "time":
                    role = COPASI.CExperiment.time
                    obj_map.setRole(i, role)

                elif col in self.sbml_id_map.keys():
                    role = COPASI.CExperiment.dependent
                    obj_map.setRole(i, role)
                    obj_map.setObjectCN(i, self.sbml_id_map[col].getConcentrationReference().getCN())

                elif col.startswith('init_') and col[5:] in self.sbml_id_map.keys():
                    role = COPASI.CExperiment.independent
                    obj_map.setRole(i, role)
                    obj_map.setObjectCN(i, self.sbml_id_map[col[5:]].getInitialConcentrationReference().getCN())

                else:
                    role = COPASI.CExperiment.ignore
                    obj_map.setRole(i, role)

    def get_fit_parameters(self):
        """ Returns all fit items specified as a list of dictionaries of the form

            [ { 'name': 'km', 'start': 0.1, 'lower': 1e-6, 'upper': 1e6, 'reaction_id': 'r1'  } ...  ]

        :return: list of dictionaries with fit items
        :rtype: [{}]
        """
        result = []
        for i in range(self.problem.getOptItemSize()):
            p = self.problem.getOptItem(i)
            assert (isinstance(p, COPASI.COptItem))
            obj = self.dm.getObject(p.getObjectCN())
            if obj is None:
                continue
            name = obj.getObjectName() if obj.getObjectType() != "Reference" else obj.getObjectParent().getObjectName()

            result.append({
                'name': name,
                'start': p.getStartValue(),
                'lower': p.getLowerBoundValue(),
                'upper': p.getUpperBoundValue(),
                'reaction_id': obj.getObjectAncestor('Reaction').getSBMLId()
            })
        return result

    def set_fit_parameters(self, fit_parameters):
        """Replaces all fit items with the ones specified

        :param fit_parameters: list of dictionaries of the same form as returned by get_fit_parameters
        :return: None
        """
        assert(isinstance(self.problem, COPASI.CFitProblem))
        assert (isinstance(self.task, COPASI.CFitTask))
        assert (isinstance(self.dm, COPASI.CDataModel))

        for i in range(self.problem.getOptItemSize()):
            self.problem.removeOptItem(0)

        for item in fit_parameters:
            if 'name' not in item:
                continue

            cn = self._get_cn_for_item(item)
            if cn is None:
                continue

            fit_item = self.problem.addFitItem(cn)
            assert (isinstance(fit_item, COPASI.CFitItem))
            if 'lower' in item:
                fit_item.setLowerBound(COPASI.CCommonName(str(item['lower'])))
            if 'upper' in item:
                fit_item.setUpperBound(COPASI.CCommonName(str(item['upper'])))
            if 'start' in item:
                fit_item.setStartValue(float(item['start']))

    def optimize(self):
        """ Carries out the Parameter estimation
        :return: None
        """
        # run optimization
        self.task.initialize(COPASI.CCopasiTask.OUTPUT_UI)
        self.task.process(True)
        self.task.restore()

    def update_enzymeml_doc(self):
        """ Updates the enzyme ml document with the values from last optimization run

        :return: None
        """
        assert (isinstance(self.problem, COPASI.CFitProblem))
        results = self.problem.getSolutionVariables()

        logging.debug('OBJ: {0}'.format(self.problem.getSolutionValue()))
        logging.debug('RMS: {0}'.format(self.problem.getRMS()))

        for i in range(self.problem.getOptItemSize()):
            item = self.problem.getOptItem(i)
            obj = self.dm.getObject(item.getObjectCN())
            if obj is None:
                continue

            name = obj.getObjectName() if obj.getObjectType() != 'Reference' else obj.getObjectParent().getObjectName()
            value = results.get(i)
            logging.debug(name, value)

            reaction = obj.getObjectAncestor('Reaction')
            if reaction is not None:
                model = self.reaction_data[reaction.getSBMLId()][0]
                for p in model.parameters:
                    if p.name == name:
                        p.value = value
                        break

    def _set_default_items(self):
        """ Initializes fit items from the local parameters specified in the reaction_data

        :return: None
        """
        for reaction_id, data in self.reaction_data.items():
            r = self.sbml_id_map[reaction_id]
            assert (isinstance(r, COPASI.CReaction))
            for p in self.reaction_data[reaction_id][0].parameters:
                obj = r.getParameterObjects(p.name)[0].getObject(COPASI.CCommonName('Reference=Value'))
                cn = obj.getCN()
                fit_item = self.problem.addFitItem(cn)
                assert (isinstance(fit_item, COPASI.CFitItem))
                fit_item.setLowerBound(COPASI.CCommonName(str(1e-6)))
                fit_item.setUpperBound(COPASI.CCommonName(str(1e6)))
                fit_item.setStartValue(float(p.value))


if __name__ == '__main__':
    this_dir = os.path.dirname(__file__)
    filename = os.path.join(this_dir + "/../../", "examples/ThinLayers/COPASI/3IZNOK_SIMULATED.omex")
    assert os.path.exists(filename)

    thin_layer = ThinLayerCopasi(
        path=filename,
        outdir='./out'
    )

    thin_layer.optimize()
    thin_layer.update_enzymeml_doc()
