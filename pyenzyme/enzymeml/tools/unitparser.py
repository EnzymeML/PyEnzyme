import re

class UnitParser(object):
    
        def __init__(self):
            
            self.__prefixDict = {
                
                "femto": "f", 
                "pico": "p",
                "nano": "n",
                "micro": "u",
                "milli": "m",
                "mili": "m",
                "centi": "c",
                "deci": "d",
                "kilo": "k"
                
                }
      
        def parse(self, exp_string ):
            
            # reformat string
            exp_string = self.__exponentString(exp_string)
            # split by exponents
            regex = "([a-zA-Z]*)([-+][\d]*)"
            regex = regex.replace(' ', '')
        
            unit_tup = re.findall(regex, exp_string)
            return [ self.__getPrefix( tup[0], tup[-1] ) for tup in unit_tup ]
        
        def getExponentString(self, string):
            
            string = string.split('/')
            
            if len(string) == 2:
                nom = string[0].split(' ')[0:-1]
                den = string[1].split(' ')[1::]

            elif len(string) == 1:
                nom = string
                den = []
                
            return "".join(  [ self.__reformatString(unit, "+") for unit in nom ] +  [self.__reformatString(unit, "-") for unit in den ]  )
    
        def __reformatString(self, string, pre):
            regex = "([a-zA-z]*)([-+]?\d*)"
            groups = re.findall(regex, string)
            
            exp_string = ""
            
            for unit, exponent in groups:
                
                if len(unit) > 0:
        
                    if len(exponent) == 1:
                        exp_string += unit + pre + exponent
        
                    elif "+" in exponent or "-" in exponent:
                        exp_string += unit + exponent
        
                    else:
                        exp_string += unit + "%s1" % pre
            
            return exp_string
        
        def __exponentString(self, string):
    
            string = string.split('/')
            
            if len(string) == 2:
                nom = string[0].split(' ')
                den = string[1].split(' ')

            elif len(string) == 1:
                nom = string
                den = []
                
            return "".join(  [ self.__reformatString(unit, "+") for unit in nom ] +  [self.__reformatString(unit, "-") for unit in den ]  )
        
        def __getPrefix(self, string, exponent):
            regex = "^([a-zA-Z]*)(C|celsius|K|kelvin|M|molar|mole|g|gram|l|L|litre|liter|s|seconds|second|h|hour|hours)$"
            string = string.lower()[0:-1] + string[-1]
            
            try:
                prefix = re.findall(regex, string)[0][0]
                
                if len(prefix) > 1:
                    prefix = self.__prefixDict[prefix.lower()]
                
                unit = re.findall(regex, string)[0][1]
                
                return ( prefix, unit, exponent )
            
            except IndexError:
                unit = re.findall(regex, string)[0][0]
                return ( "NONE", unit, exponent )
        
        