# """
# File: TL_Copasi.py
# Project: ThinLayers
# Author: Jan Range
# Author: Frank Bergmann
# License: BSD-2 clause
# -----
# Last Modified: Wednesday June 23rd 2021 10:25:11 pm
# Modified By: Jan Range (<jan.range@simtech.uni-stuttgart.de>)
# -----
# Copyright (c) 2021 Institute of Biochemistry and Technical Biochemistry Stuttgart
# """

"""
This module contains the COPASI ThinLayer:

To use it, simply instantiate it using an EnzymeML Document. This will estimate all parameters of the enzyme ml
document (all temporary data will be stored in working_dir).

    >>> tl = ThinLayerCopasi(path='Model4.omex', outdir='./working_dir')
    >>> tl.optimize()

    This would return a pandas dataframe with the fit found, to write it into a new document you'd use:

    >>> new_doc = tl.write()


In order to change the settings of the parameter estimation, or to change the loaded model we recommend to use
`basico <https://basico.readthedocs.io/>`_. so after initializing the thinlayer, you'd load the model into basico.
For example here is how you'd switch the method to particle swarm:

    >>> from basico import *
    >>> tl = ThinLayerCopasi(path='Model4.omex', outdir='./working_dir')
    >>> set_current_model(tl.dm)
    >>> set_task_settings(T.PARAMETER_ESTIMATION,
    ...              {
    ...                  'method': {'name': PE.PARTICLE_SWARM }
    ...              })

If the modle is loaded into basico, you can easily plot the results as well. The COPASI file (.cps) in the working
directory can also be directly used from the COPASI Graphical User Interface.

"""

import logging
from typing import Union, Optional

from pyenzyme.thinlayers import BaseThinLayer
import os
import pandas as pd
from builtins import enumerate

_COPASI_IMPORT_ERROR = None
try:
    import COPASI
except ModuleNotFoundError as e:
    _COPASI_IMPORT_ERROR = """
    ThinLayerCopasi is not available. 
    To use it, please install the following dependencies:
    {}
    """.format(e)

log = logging.getLogger(__name__)


class ThinLayerCopasi(BaseThinLayer):

    def __init__(self, path, outdir,
                 measurement_ids: Union[str, list] = "all",
                 init_file: Optional[str] = None):
        """
        Initializes a new instance of the COPASI thin layer, by loading the EnzymeML file
        specified in `path` and creating a COPASI file (+ data) in `outdir`.

        :param path: the enzyme ml document to load
        :param outdir: the output dir
        :param measurement_ids: the measurement ids or all
        :param init_file: optional initialization file for fit items

        """
        # check dependencies
        if _COPASI_IMPORT_ERROR:
            raise RuntimeError(_COPASI_IMPORT_ERROR)

        # initialize base class, let it do the reading
        BaseThinLayer.__init__(
            self, path, measurement_ids, init_file=init_file)
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
            log.error(COPASI.CCopasiMessage.getAllMessageText())

        # maps
        self._init_maps()

        # variables
        self.model = self.dm.getModel()
        self.task = self.dm.getTask('Parameter Estimation')
        self.task.setScheduled(True)
        self.task.setUpdateModel(False)
        self.task.setMethodType(COPASI.CTaskEnum.Method_LevenbergMarquardt)
        self.problem = self.task.getProblem()
        self.problem.setCalculateStatistics(True)
        self.exp_set = self.problem.getExperimentSet()

        # read in experiments
        self._import_experiments()

        # set all parameters as fit items
        if init_file is None:
            self._set_default_items()
        else:
            self._set_default_items_from_init_file()

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

        :param item: dictionary with 'name' and optionally 'reaction_id'
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
            sbml_ids = measurement_dict['data'].columns.to_list()

            data = measurement_dict['data']

            for k, v in measurement_dict['initConc'].items():
                data = data.join(pd.DataFrame({'init_{0}'.format(k): [v[0]]}))
                sbml_ids.append('init_{0}'.format(k))
                # validate value
                if k in data.columns:
                    initial_value = data[data['time'] == 0.0][k]
                    if not initial_value.empty and float(initial_value) != v[0]:
                        log.warning(f'The initial value of "{k}" in experiment "{measurement_id}" '
                                    f'is inconsistent with the specified initial concentration: '
                                    f'{float(initial_value)} != {v[0]}')

            exp_filename = os.path.abspath(os.path.join(
                self.working_dir, measurement_id + '.tsv'))

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
                    obj_map.setObjectCN(i, self.sbml_id_map[col]
                                        .getConcentrationReference().getCN().getString())

                elif col.startswith('init_') and col[5:] in self.sbml_id_map.keys():
                    role = COPASI.CExperiment.independent
                    obj_map.setRole(i, role)
                    obj_map.setObjectCN(i, self.sbml_id_map[col[5:]]
                                        .getInitialConcentrationReference().getCN().getString())

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
            name = obj.getObjectName() if obj.getObjectType(
            ) != "Reference" else obj.getObjectParent().getObjectName()

            r = obj.getObjectAncestor('Reaction')
            reaction_id = r.getSBMLId() if r else None

            result.append({
                'name': name,
                'start': p.getStartValue(),
                'lower': p.getLowerBoundValue(),
                'upper': p.getUpperBoundValue(),
                'reaction_id': reaction_id
            })
        return result

    def set_fit_parameters(self, fit_parameters):
        """Replaces all fit items with the ones specified

        :param fit_parameters: list of dictionaries of the same form as returned by get_fit_parameters
        :return: None
        """
        assert (isinstance(self.problem, COPASI.CFitProblem))
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

    def _get_result(self):
        """Utility function adding a value column to the fit items

        :return: pandas dataframe with the result of the fit
        :rtype: pandas.DataFrame
        """
        fit_items = self.get_fit_parameters()
        new_values = [val for val in self.problem.getSolutionVariables()]
        sd_values = [val for val in self.problem.getVariableStdDeviations()]
        if len(fit_items) != len(new_values):
            logging.error('No results available yet, run `optimize` first.')
            return None

        for i, vals in enumerate(fit_items):
            vals['value'] = new_values[i]
            vals['std_deviation'] = sd_values[i]

        df = pd.DataFrame(data=fit_items).set_index('name')
        return df

    def optimize(self, update_model=False):
        """ Carries out the Parameter estimation

        :param update_model: optional argument, indicating whether to
               update the model, so another optimization run would start
               with the solution found from the first run.

        :return: Pandas DataFrame with the results

        """
        # run optimization
        self.task.setUpdateModel(update_model)
        if not self.task.initializeRaw(COPASI.CCopasiTask.OUTPUT_UI):
            log.error(COPASI.CCopasiMessage.getFirstMessage().getAllMessageText())
        if not self.task.processRaw(True):
            log.error(COPASI.CCopasiMessage.getFirstMessage().getAllMessageText())
        self.task.restore()

        return self._get_result()

    def write(self):
        """Writes the estimated parameters to a copy of the EnzymeMLDocument"""

        nu_enzmldoc = self.enzmldoc.copy(deep=True)

        assert (isinstance(self.problem, COPASI.CFitProblem))
        results = self.problem.getSolutionVariables()
        if self.problem.getOptItemSize() != results.size():
            log.error('The optimization was not run yet, no update can be made')
            return nu_enzmldoc

        log.debug('OBJ: {0}'.format(self.problem.getSolutionValue()))
        log.debug('RMS: {0}'.format(self.problem.getRMS()))

        for i in range(self.problem.getOptItemSize()):
            item = self.problem.getOptItem(i)
            obj = self.dm.getObject(item.getObjectCN())
            if obj is None:
                continue

            name = obj.getObjectName() if obj.getObjectType(
            ) != 'Reference' else obj.getObjectParent().getObjectName()

            value = results.get(i)

            reaction = obj.getObjectAncestor('Reaction')
            if reaction is not None:
                enz_reaction = nu_enzmldoc.getReaction(reaction.getSBMLId())
                if enz_reaction:
                    parameter = enz_reaction.model.getParameter(name)
                    parameter.value = value
            else:
                p = nu_enzmldoc.global_parameters.get(name)
                p.value = value

        return nu_enzmldoc

    def _set_default_items(self):
        """ Initializes fit items from the local parameters specified in the reaction_data

        :return: None
        """
        for reaction_id, data in self.reaction_data.items():
            r = self.sbml_id_map[reaction_id]
            assert (isinstance(r, COPASI.CReaction))
            for p in self.reaction_data[reaction_id][0].parameters:
                obj = r.getParameterObjects(p.name)[0].getObject(
                    COPASI.CCommonName('Reference=Value'))
                cn = obj.getCN()
                fit_item = self.problem.addFitItem(cn)
                assert (isinstance(fit_item, COPASI.CFitItem))
                fit_item.setLowerBound(COPASI.CCommonName(str(1e-6)))
                fit_item.setUpperBound(COPASI.CCommonName(str(1e6)))
                fit_item.setStartValue(float(p.value))

    def _set_default_items_from_init_file(self):
        """ Use this to create a default template, when an init file was passed to the thin layer
            and it has been already applied

        :return: None
        """
        assert (isinstance(self.problem, COPASI.CFitProblem))

        # remove old items
        while self.problem.getOptItemSize() > 0:
            self.problem.removeOptItem(0)

        for global_param in self.global_parameters.values():

            if not global_param.lower or not global_param.upper:
                # nan values used to indicate that this should not be fitted
                continue

            mv = self.dm.getModel().getModelValue(global_param.name)
            if not mv:
                log.warning(
                    "No global parameter {0} in the model".format(global_param.name))
                continue

            value = global_param.value if global_param.value else global_param.initial_value

            if not value:
                raise ValueError(
                    f"Neither initial_value nor value given for parameter {global_param.name} in global parameters"
                )

            cn = mv.getInitialValueReference().getCN()
            fit_item = self.problem.addFitItem(cn)
            assert (isinstance(fit_item, COPASI.CFitItem))
            fit_item.setLowerBound(COPASI.CCommonName(str(global_param.lower)))
            fit_item.setUpperBound(COPASI.CCommonName(str(global_param.upper)))
            fit_item.setStartValue(float(value))

        for reaction_id, (model, _) in self.reaction_data.items():
            r = self.sbml_id_map[reaction_id]
            assert (isinstance(r, COPASI.CReaction))
            for p in model.parameters:
                if p.is_global:
                    continue

                if not p.lower or not p.upper:
                    # nan values used to indicate that this should not be fitted
                    continue

                value = p.value if p.value else p.initial_value

                if not value:
                    raise ValueError(
                        f"Neither initial_value nor value given for parameter {p.name} in reaction {reaction_id}"
                    )

                obj = r.getParameterObjects(p.name)[0].getObject(
                    COPASI.CCommonName('Reference=Value'))
                cn = obj.getCN()
                fit_item = self.problem.addFitItem(cn)
                assert (isinstance(fit_item, COPASI.CFitItem))
                fit_item.setLowerBound(COPASI.CCommonName(str(p.lower)))
                fit_item.setUpperBound(COPASI.CCommonName(str(p.upper)))
                fit_item.setStartValue(float(value))


if __name__ == '__main__':
    this_dir = os.path.dirname(__file__)
    filename = os.path.join(this_dir + "/../../",
                            "examples/ThinLayers/COPASI/3IZNOK_Simulated.omex")
    assert os.path.exists(filename)

    thin_layer = ThinLayerCopasi(
        path=filename,
        outdir='./out'
    )

    thin_layer.optimize()
    thin_layer.write()
