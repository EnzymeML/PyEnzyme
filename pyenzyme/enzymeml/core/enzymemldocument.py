'''
Created on 09.06.2020

@author: JR
'''

## TODO - AddXXX Functions

from pyenzyme.enzymeml.core.functionalities import TypeChecker
from pyenzyme.enzymeml.core.reactant import Reactant
from pyenzyme.enzymeml.core.creator import Creator
from pyenzyme.enzymeml.core.protein import Protein
from pyenzyme.enzymeml.core.vessel import Vessel
from pyenzyme.enzymeml.core.enzymereaction import EnzymeReaction
from pyenzyme.enzymeml.tools.unitcreator import UnitCreator


class EnzymeMLDocument(object):

    def __init__(self, name, level=3, version=2):
        '''
        Super class of an enzymeml document, holding all relevant information
        
        Args:
            String name: Document name
            Integer level: SBML Level
            Integer version: SBML Version
        '''
        
        self.setName(name)
        self.setLevel(level)
        self.setVersion(version)
        
        self.setProteinDict(dict())
        self.setReactantDict(dict())
        self.setReactionDict(dict())
        self.setUnitDict(dict())
        self.setConcDict(dict())

    def getDoi(self):
        return self.__doi


    def getPubmedID(self):
        return self.__pubmedID


    def getUrl(self):
        return self.__url


    def setDoi(self, doi):
        if "https://identifiers.org/doi:" in TypeChecker(doi, str):
            self.__doi = doi
        else:
            self.__doi = "https://identifiers.org/doi:" + doi


    def setPubmedID(self, pubmedID):
        if "https://identifiers.org/pubmed:" in pubmedID:
            self.__pubmedID = TypeChecker(pubmedID, str)
        else:
            self.__pubmedID = "https://identifiers.org/pubmed:" + TypeChecker(pubmedID, str)


    def setUrl(self, url):
        self.__url = TypeChecker(url, str)


    def delDoi(self):
        del self.__doi


    def delPubmedID(self):
        del self.__pubmedID


    def delUrl(self):
        del self.__url


    def getConcDict(self):
        return self.__ConcDict


    def setConcDict(self, value):
        self.__ConcDict = value


    def delConcDict(self):
        del self.__ConcDict

        
    def __getReplicateUnits(self, reaction):
        
        # update replicate units
        for i, tup in enumerate(reaction.getEducts()):
            for j, repl in enumerate(tup[3]):
                
                time_unit = repl.getTimeUnit()
                data_unit = repl.getDataUnit()
                
                if data_unit not in self.getUnitDict().keys(): 
                    reaction.getEducts()[i][3][j].setDataUnit( UnitCreator().getUnit(data_unit, self) )               
                if time_unit not in self.getUnitDict().keys():
                    reaction.getEducts()[i][3][j].setTimeUnit( UnitCreator().getUnit(time_unit, self) )
                if repl.getInitConc() == 'NONE':
                    reaction.getEducts()[i][3][j].setInitConc( self.getReactant( repl.getReactant() ).getInitConc() )
                
        # update replicate units
        for i, tup in enumerate(reaction.getProducts()):
            for j, repl in enumerate(tup[3]):
                
                time_unit = repl.getTimeUnit()
                data_unit = repl.getDataUnit()
                
                if data_unit not in self.getUnitDict().keys(): 
                    reaction.getProducts()[i][3][j].setDataUnit( UnitCreator().getUnit(data_unit, self) )
                if time_unit not in self.getUnitDict().keys():
                    reaction.getProducts()[i][3][j].setTimeUnit( UnitCreator().getUnit(time_unit, self) )
                if repl.getInitConc() == 'NONE':
                    reaction.getProducts()[i][3][j].setInitConc( self.getReactant( repl.getReactant() ).getInitConc() )
                
        # update replicate units
        for i, tup in enumerate(reaction.getModifiers()):
            for j, repl in enumerate(tup[3]):
                
                time_unit = repl.getTimeUnit()
                data_unit = repl.getDataUnit()
                
                if data_unit not in self.getUnitDict().keys(): 
                    reaction.getModifiers()[i][3][j].setDataUnit( UnitCreator().getUnit(data_unit, self) )
                if time_unit not in self.getUnitDict().keys():
                    reaction.getModifiers()[i][3][j].setTimeUnit( UnitCreator().getUnit(time_unit, self) )
                if repl.getInitConc() == 'NONE':
                    reaction.getModifiers()[i][3][j].setInitConc( self.getReactant( repl.getReactant() ).getInitConc() )
        
        
    def printReactions(self):
        print('>>> Reactions')
        for key, item in self.__ReactionDict.items():
            print('    ID: %s \t Name: %s' % ( key, item.getName() ))
            
    def printUnits(self):
        print('>>> Units')
        for key, item in self.__UnitDict.items():
            print('    ID: %s \t Name: %s' % ( key, item.getName() ))
            
    def printReactants(self):
        print('>>> Reactants')
        for key, item in self.__ReactantDict.items():
            print('    ID: %s \t Name: %s' % ( key, item.getName() ))
            
    def printProteins(self):
        print('>>> Proteins')
        for key, item in self.__ProteinDict.items():
            print('    ID: %s \t Name: %s' % ( key, item.getName() ))
        
    def getReaction(self, id_, by_id=True):
        
        '''
        Returns EnzymeReaction object indexed by it ID
        
        Args:
            String id_: Reaction ID
        '''
        
        if by_id:
            
            if id_ in self.__ReactionDict.keys():
                return self.__ReactionDict[id_]

            raise KeyError('Reaction %s not found in EnzymeML document %s' % ( id_, self.__name ))
            
        else:
            for reaction in self.__ReactionDict.values():
                if id_ == reaction.getName():
                    return reaction

            raise KeyError('Reaction %s not found in EnzymeML document %s' % ( id_, self.__name ))
        
    def getReactant(self, id_, by_id=True):
        
        '''
        Returns Reactant object indexed by it ID
        
        Args:
            String id_: Reactant ID
        '''
        
        if by_id:
            
            if id_ in self.__ReactantDict.keys():
                return self.__ReactantDict[id_]

            raise KeyError('Reactant %s not found in EnzymeML document %s' % ( id_, self.__name ))
            
        else:
            for reactant in self.__ReactantDict.values():
                if id_ == reactant.getName():
                    return reactant

            raise KeyError('Reactant %s not found in EnzymeML document %s' % ( id_, self.__name ))
        
    def getProtein(self, id_, by_id=True):
        
        '''
        Returns Protein object indexed by it ID
        
        Args:
            String id_: Protein ID
        '''
        if by_id:
               
            if id_ in self.__ProteinDict.keys():
                return self.__ProteinDict[id_]

            raise KeyError('Protein %s not found in EnzymeML document %s' % ( id_, self.__name ))
            
        else:
            for protein in self.__ProteinDict.values():
                if id_ == protein.getName():
                    return protein

            raise KeyError('Protein %s not found in EnzymeML document %s' % ( id_, self.__name ))
    
    def addReactant(self, reactant, use_parser=True, custom_id='NULL'):
        
        '''
        Adds Reactant class to EnzymeMLDocument reactant dictionary
        
        Args:
            Reactant reactant: Object describing an EnzymeML reactant.
        '''
        
        TypeChecker(reactant, Reactant)
        
        index = 0
        
        if custom_id == "NULL":
            id_ = "s%i" % index
        else:
            id_ = custom_id
        
        while True:
            
            if id_ not in self.__ReactantDict.keys():
                
                if use_parser:
                    
                    # Automatically set UnitCreator
                    if reactant.getSubstanceunits() != 'NAN':
                        reactant.setSubstanceunits( 
                            
                            UnitCreator().getUnit( reactant.getSubstanceunits(), self) 
                            
                            )
                    
                reactant.setId(id_)   
                reactant.setSboterm("SBO:0000247")
                self.__ReactantDict[reactant.getId()] = reactant
                
                return id_
                
            else:
                index += 1
                id_ = "s%i" % index
        
    def addProtein(self, protein, use_parser=True):
        
        '''
        Adds Protein class to EnzymeMLDocument protein dictionary
        
        Args:
            Protein protein: Object describing an EnzymeML protein.
        '''
                
        TypeChecker(protein, Protein)
        
        index = 0
        id_ = "p%i" % index
        while True:
            
            if id_ not in self.__ProteinDict.keys():
                
                if use_parser:
                    
                    # Automatically set UnitCreator
                    protein.setSubstanceUnits( 
                        
                        UnitCreator().getUnit( protein.getSubstanceUnits(), self) 
                        
                        )
                    
                protein.setId(id_)
                protein.setSboterm("SBO:0000252")
                self.__ProteinDict[protein.getId()] = protein
                
                return id_
            else:
                index += 1
                id_ = "p%i" % index
                
    
    def addReaction(self, reaction, use_parser=True):
        
        '''
        Adds Reaction class to EnzymeMLDocument reaction dictionary
        
        Args:
            Reaction reaction: Object describing an EnzymeML reaction.
        '''
            
        TypeChecker(reaction, EnzymeReaction)
        
        index = 0
        id_ = "r%i" % index
        while True:
            
            if id_ not in self.__ReactionDict.keys():
                
                if use_parser:
                    
                    # Automatically set UnitCreator
                    self.__getReplicateUnits(reaction)
                    
                reaction.setId(id_)
                reaction.setTemperature( reaction.getTemperature() + 273.15 )
                reaction.setTempunit( 
                    UnitCreator().getUnit( reaction.getTempunit(), self) 
                    )
                
                # set model units
                try:
                    for key, item in reaction.getModel().getParameters().items():
                        
                        reaction.getModel().getParameters()[key] = (item[0], UnitCreator().getUnit( item[1] , self) )
                        
                except Exception as e:
                    print(e)

                self.__ReactionDict[reaction.getId()] = reaction
                
                return id_
            else:
                index += 1
                id_ = "r%i" % index
    
    def get_created(self):
        return self.__created


    def getModified(self):
        return self.__modified


    def setCreated(self, date):
        self.__created = TypeChecker(date, str)


    def setModified(self, date):
        self.__modified = TypeChecker(date, str)


    def delCreated(self):
        del self.__created


    def delModified(self):
        del self.__modified


    def getCreator(self):
        return self.__creator


    def setCreator(self, creators):
        '''
        Args:
            Creator creators: Single instance or list of Creator class describing user meta information 
        '''
        
        if type(creators) == list:
            self.__creator = [ TypeChecker(creator, Creator) for creator in creators ]
        else:
            self.__creator = [TypeChecker(creators, Creator)]


    def delCreator(self):
        del self.__creator


    def getVessel(self):
        return self.__vessel


    def setVessel(self, vessel, use_parser=True):
        
        '''
        Adds Vessel class to EnzymeMLDocument
        
        Args:
            Vessel vessel: Object describing an EnzymeML vessel.
        '''
        
        # Automatically set unit
        if use_parser:
            
            vessel.setUnit( 
                
                UnitCreator().getUnit( vessel.getUnit(), self) 
                
                )
            
            
        self.__vessel = TypeChecker(vessel, Vessel)


    def delVessel(self):
        del self.__vessel


    def getName(self):
        return self.__name


    def getLevel(self):
        return self.__level


    def getVersion(self):
        return self.__version


    def getProteinDict(self):
        return self.__ProteinDict


    def getReactantDict(self):
        return self.__ReactantDict


    def getReactionDict(self):
        return self.__ReactionDict


    def getUnitDict(self):
        return self.__UnitDict


    def setName(self, value):
        '''
        Args:
            String value: Name of EnzymeMLDocument
        '''
        self.__name = value


    def setLevel(self, level):
        
        if 1 <= TypeChecker(level, int) <= 3:
            self.__level = level
        else:
            raise IndexError("Level out of bounds. SBML level is defined from 1 to 3.")


    def setVersion(self, version):
        self.__version = TypeChecker(version, int)


    def setProteinDict(self, proteinDict):
        self.__ProteinDict = TypeChecker(proteinDict, dict)


    def setReactantDict(self, reactantDict):
        self.__ReactantDict = TypeChecker(reactantDict, dict)


    def setReactionDict(self, reactionDict):
        self.__ReactionDict = TypeChecker(reactionDict, dict)


    def setUnitDict(self, unitDict):
        self.__UnitDict = TypeChecker(unitDict, dict)


    def delName(self):
        del self.__name


    def delLevel(self):
        del self.__level


    def delVersion(self):
        del self.__version


    def delProteinDict(self):
        del self.__ProteinDict


    def delReactantDict(self):
        del self.__ReactantDict


    def delReactionDict(self):
        del self.__ReactionDict


    def delUnitDict(self):
        del self.__UnitDict

    _name = property(getName, setName, delName, "_name's docstring")
    _level = property(getLevel, setLevel, delLevel, "_level's docstring")
    _version = property(getVersion, setVersion, delVersion, "_version's docstring")
    _ProteinDict = property(getProteinDict, setProteinDict, delProteinDict, "_ProteinDict's docstring")
    _ReactantDict = property(getReactantDict, setReactantDict, delReactantDict, "_ReactantDict's docstring")
    _ReactionDict = property(getReactionDict, setReactionDict, delReactionDict, "_ReactionDict's docstring")
    _UnitDict = property(getUnitDict, setUnitDict, delUnitDict, "_UnitDict's docstring")
    _vessel = property(getVessel, setVessel, delVessel, "_vessel's docstring")
    _creator = property(getCreator, setCreator, delCreator, "_creator's docstring")
    _created = property(get_created, setCreated, delCreated, "_created's docstring")
    _modified = property(getModified, setModified, delModified, "_modified's docstring")
    _ConcDict = property(getConcDict, setConcDict, delConcDict, "_ConcDict's docstring")
    _doi = property(getDoi, setDoi, delDoi, "_doi's docstring")
    _pubmedID = property(getPubmedID, setPubmedID, delPubmedID, "_pubmedID's docstring")
    _url = property(getUrl, setUrl, delUrl, "_url's docstring")
        
        