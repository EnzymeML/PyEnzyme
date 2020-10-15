'''
Created on 10.06.2020

@author: JR
'''

from pyenzyme.enzymeml.core.functionalities import TypeChecker
from pandas.core.series import Series


class Replicate(object):

    def __init__(self, replica, reactant, type_, data_unit, time_unit, init_conc="NONE"):

        '''
        Object describing an EnzymeML replicate.
        
        Args:
            String replica: Replicate internal identifier
            String species: Species internal identifier
            String type: Type of time series data
            String data_unit: Unit definition for data 
            String time_unit: Unit definition for time
        '''
        
        self.setReplica(replica)
        self.setReactant(reactant)
        self.setType(type_)
        self.setDataUnit(data_unit)
        self.setTimeUnit(time_unit)
        self.setInitConc(init_conc)

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


    def getData(self):
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
            Pandas.Series data: Either raw data  plus time (List or Numpy array) or Pandas Series with time data as index
            List/NumpyArray time: Additional time data 
        '''
        
        if time is None:     
            self.__data = TypeChecker(data, Series)
        else:
            dat = Series(data)
            dat.Index = time
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

    _replica = property(getReplica, setReplica, delReplica, "_replica's docstring")
    _type = property(getType, setType, delType, "_type's docstring")
    _data_unit = property(getDataUnit, setDataUnit, delDataUnit, "_data_unit's docstring")
    _time_unit = property(getTimeUnit, setTimeUnit, delTimeUnit, "_time_unit's docstring")
    _data = property(getData, setData, delData, "_data's docstring")
    _reactant = property(None, None, None, "_reactant's docstring")
    _init_conc = property(getInitConc, setInitConc, delInitConc, "_init_conc's docstring")
        
        
        
        
        
        

        
        
        