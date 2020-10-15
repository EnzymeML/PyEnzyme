'''
Created on 15.08.2020

@author: JR
'''
import libsbml
from pyenzyme.enzymeml.core.unitdef import UnitDef
from pyenzyme.enzymeml.tools.unitparser import UnitParser

class UnitCreator(object):
    
    def __init__(self):
        
        self.__functionDict = {
            
            "M": self.__Molar,
            "m": self.__Mole,
            "mole": self.__Mole,
            "l": self.__Volume,
            "liter": self.__Volume,
            "litre": self.__Volume,
            "g": self.__Amount,
            "gram": self.__Amount,
            "s": self.__Seconds,
            "second": self.__Seconds,
            "seconds": self.__Seconds,
            "min": self.__Minutes,
            "minute": self.__Minutes,
            "minutes": self.__Minutes,
            "h": self.__Hours,
            "hour": self.__Hours,
            "hours": self.__Hours,
            "C": self.__Celsius,
            "c": self.__Celsius,
            "celsius": self.__Celsius,
            "K": self.__Kelvin,
            "kelvin": self.__Kelvin
            
            
            }

    def getUnit(self, unit_string, enzmldoc):
        
        
        '''
        Args:
            String unit_string: Standard short form of unit
        '''
        
        index = 0
        while True:
            
            id_ = "u%i" % index
            
            if id_ not in enzmldoc.getUnitDict().keys():
                break
            else:
                index += 1
        
        '''       
        # check if its already a unit
        regex = "[u\d]"
        f = lambda x: re.findall(regex, x)
        res = len(f(unit_string))
        print("LELE", unit_string, res)
        if 2 > 1:
            return unit_string
        '''
                     
        # Call unit parser to identify units
        parser = UnitParser()
        units = sorted(parser.parse(unit_string))
        
        # Check if there is already a similar unit defined
        if self.__checkFootprints(enzmldoc, units) != "NEW":
            
            return self.__checkFootprints(enzmldoc, units)
        
        # Initialize UnitDef
        name = " ".join( ["%s%s %s" % ( prefix, baseunit, exponent ) for prefix, baseunit, exponent in units ] )
        unitdef = UnitDef(name, id_, "NONE")
        unitdef.setFootprint(units)
        
        for prefix, baseunit, exponent in units:
            self.__functionDict[baseunit]( unitdef, prefix, exponent )
        
        enzmldoc.getUnitDict()[unitdef.getId()] = unitdef
        
        return unitdef.getId()
    
    def __checkFootprints(self, enzmldoc, footprint):
        
        unitdict = enzmldoc.getUnitDict()
        
        def __compare(f1, f2):
            return sum( [ 0 if tup1 == tup2 else 1 for tup1, tup2 in zip( sorted(f1), sorted(f2) ) ] )
        
        for unitdef in unitdict:
            if __compare( unitdict[unitdef].getFootprint() , footprint) == 0:

                return unitdict[unitdef].getId()
            
        return "NEW"
            
    def __Mole(self, unitdef, prefix, exponent):
        
        kind = libsbml.UNIT_KIND_MOLE
        scale = self.__getPrefix(prefix)
        multiplier = 1
        
        unitdef.addBaseUnit( kind, exponent, scale, multiplier )
        
    def __Molar(self, unitdef, prefix, exponent):
        
        self.__Mole(unitdef, prefix, exponent)
        
        kind = libsbml.UNIT_KIND_LITRE
        scale = 1
        multiplier = 1
        
        unitdef.addBaseUnit( kind, -1, scale, multiplier )
        
    def __Volume(self, unitdef, prefix, exponent):
        
        kind = libsbml.UNIT_KIND_LITRE
        scale = self.__getPrefix(prefix)
        multiplier = 1
        
        unitdef.addBaseUnit( kind, exponent, scale, multiplier )
        
    def __Amount(self, unitdef, prefix, exponent):
        
        kind = libsbml.UNIT_KIND_GRAM
        scale = self.__getPrefix(prefix)
        multiplier = 1
        
        unitdef.addBaseUnit( kind, exponent, scale, multiplier )
        
    def __Seconds(self, unitdef, prefix, exponent):
        
        kind = libsbml.UNIT_KIND_SECOND
        scale = 1
        multiplier = 1
        
        unitdef.addBaseUnit( kind, exponent, scale, multiplier )
        
    def __Minutes(self, unitdef, prefix=None, exponent=1):
        
        kind = libsbml.UNIT_KIND_SECOND
        scale = 1
        multiplier = 60
        
        unitdef.addBaseUnit( kind, exponent, scale, multiplier )
        
    def __Hours(self, unitdef, prefix=None, exponent=1):
        
        kind = libsbml.UNIT_KIND_SECOND
        scale = 1
        multiplier = 60*60
        
        unitdef.addBaseUnit( kind, exponent, scale, multiplier )
        
    def __Celsius(self, unitdef, prefix=None, exponent=1):
        
        kind = libsbml.UNIT_KIND_KELVIN
        scale = 1
        multiplier = 1
        
        unitdef.addBaseUnit( kind, exponent, scale, multiplier )
        
    def __Kelvin(self, unitdef, prefix=None, exponent=1):
        
        kind = libsbml.UNIT_KIND_KELVIN
        scale = 1
        multiplier = 1
        
        unitdef.addBaseUnit( kind, exponent, scale, multiplier )
        
    def __getPrefix(self, prefix):
        
        if prefix == "f":
            return -15
        elif prefix == "p":
            return -12
        elif prefix == "n":
            return -9
        elif prefix == "u":
            return -6
        elif prefix == "m":
            return -3
        elif prefix == "c":
            return -2
        elif prefix == "d":
            return -1
        elif prefix == "k":
            return 3
        elif len(prefix) == 0:
            return 1
        else:
            raise KeyError("Prefix %s is unknown. Please define unit manually" % prefix)
        
    def __Time(self, baseunit):
        
        if baseunit == "s" or baseunit == "sec" or baseunit == "seconds":
            return 1
        elif baseunit == "m" or baseunit == "min" or baseunit == "minutes":
            return 60
        elif baseunit == "h" or baseunit == "hours":
            return 60*60
        else:
            raise KeyError("Time unit %s is unknown. Please define unit manually" % baseunit)
        
        
        
        