'''
File: replicate.py
Project: core
Author: Jan Range
License: BSD-2 clause
-----
Last Modified: Tuesday June 22nd 2021 6:53:17 pm
Modified By: Jan Range (<jan.range@simtech.uni-stuttgart.de>)
-----
Copyright (c) 2021 Institute of Biochemistry and Technical Biochemistry Stuttgart
'''

from pyenzyme.enzymeml.core.enzymemlbase import EnzymeMLBase
from pyenzyme.enzymeml.core.functionalities import TypeChecker
from pandas.core.series import Series

import json


class Replicate(EnzymeMLBase):

    def __init__(
        self,
        replica,
        reactant,
        type_,
        measurement,
        data_unit,
        time_unit,
        init_conc="NONE",
        data=None,
        time=None,
        isCalculated=False,
        uri=None,
        creatorId=None
    ):

        '''
        Object describing an EnzymeML replicate.

        Args:
            String replica: Replicate internal identifier
            String species: Species internal identifier
            String type: Type of time series data
            String measurement: Measurement ID
            String data_unit: Unit definition for data
            String time_unit: Unit definition for time
            List data: Raw time course data
            List time: Time values corresponding to data
            Boolean isCalculated: Recursively derived values
            String uri: Custom unique identifier
            String creatorId: Identifier to credit Creator
        '''

        # Initialize base attributes
        super().__init__(
            uri,
            creatorId
        )

        self.setReplica(replica)
        self.setReactant(reactant)
        self.setType(type_)
        self.setMeasurement(measurement)
        self.setDataUnit(data_unit)
        self.setTimeUnit(time_unit)
        self.setInitConc(init_conc)
        self.setIsCalculated(isCalculated)

        if data is not None and time is not None:
            self.setData(data, time)

    def toJSON(self, d=False, enzmldoc=False):

        def transformAttr(self):
            d = dict()
            for key, item in self.__dict__.items():
                if type(item) == Series:
                    d['data'] = list(item)
                    d['time'] = list(item.index)
                else:

                    if enzmldoc is not False:

                        if 'unit' in key:
                            if item:
                                item = enzmldoc.getUnitDict()[item].getName()
                            if not item:
                                item = "nan"

                        if "init_conc" in key:
                            val, unit = enzmldoc.getConcDict()[item]
                            item = [
                                val, enzmldoc.getUnitDict()[unit].getName()
                            ]

                    if str(item) != "nan":
                        d[key.split('__')[-1]] = item

            return d

        if d:
            return transformAttr(self)

        return json.dumps(
            self,
            default=transformAttr,
            indent=4
            )

    def setMeasurement(self, measurement):
        self.__measurement = TypeChecker(measurement, str)

    def getMeasurement(self):
        return self.__measurement

    def delMeasurement(self):
        del self.__measurement

    def setIsCalculated(self, isCalculated):
        self.__isCalculated = TypeChecker(isCalculated, bool)

    def getIsCalculated(self):
        return self.__isCalculated

    def delIsCalculated(self):
        del self.__isCalculated

    def __str__(self):
        return self.toJSON()

    def getInitConc(self):
        return self.__init_conc

    def setInitConc(self, value):
        self.__init_conc = value

    def delInitConc(self):
        del self.__init_conc

    def getReplica(self):
        return self.__replica

    def getReactant(self):
        return self.__species

    def getType(self):
        return self.__type

    def getDataUnit(self):
        return self.__data_unit

    def getTimeUnit(self):
        return self.__time_unit

    def getData(self, sep=False):
        if sep:
            time = self.__data.index.tolist()
            data = self.__data.values.tolist()
            return time, data
        return self.__data

    def setReplica(self, replica_id):
        self.__replica = TypeChecker(replica_id, str)

    def setReactant(self, reactant_id):
        self.__species = TypeChecker(reactant_id, str)

    def setType(self, type_):
        self.__type = TypeChecker(type_, str)

    def setDataUnit(self, unit_id):
        self.__data_unit = TypeChecker(unit_id, str)

    def setTimeUnit(self, unit_id):
        self.__time_unit = TypeChecker(unit_id, str)

    def setData(self, data, time=None):
        '''
        Args:
            pd.Series data: Either raw data  plus time (List or Numpy array)
                                or Pandas Series with time data as index
            List/NumpyArray time: Additional time data
        '''

        if time is None:
            self.__data = TypeChecker(data, Series)
        else:
            dat = Series(data)
            dat.index = time

            self.__data = dat

    def delReplica(self):
        del self.__replica

    def delReactant(self):
        del self.__species

    def delType(self):
        del self.__type

    def delDataUnit(self):
        del self.__data_unit

    def delTimeUnit(self):
        del self.__time_unit

    def delData(self):
        del self.__data
