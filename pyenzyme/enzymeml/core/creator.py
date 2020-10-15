'''
Created on 09.06.2020

@author: JR
'''

from pyenzyme.enzymeml.core.functionalities import TypeChecker


class Creator(object):

    def __init__(self, family_name, given_name, mail):
        
        '''
        Defines creator of EnzymeML file and experiment
        
        Args:
            String family_name:
            String given_name:
            String mail:

        '''
        
        self.setFname(family_name)
        self.setGname(given_name)
        self.setMail(mail)

    def getFname(self):
        return self.__fname


    def getGname(self):
        return self.__gname


    def getMail(self):
        return self.__mail

    def setFname(self, family_name):
        '''
        Args:
            String family_name:
        '''
        self.__fname = TypeChecker(family_name, str)


    def setGname(self, given_name):
        '''
        Args:
            String given_name:
        '''
        self.__gname = TypeChecker(given_name, str)


    def setMail(self, mail):
        '''
        Args:
            String mail:
        '''
        self.__mail = TypeChecker(mail, str)


    def delFname(self):
        del self.__fname


    def delGname(self):
        del self.__gname


    def delMail(self):
        del self.__mail


    _fname = property(getFname, setFname, delFname, "_fname's docstring")
    _gname = property(getGname, setGname, delGname, "_gname's docstring")
    _mail = property(getMail, setMail, delMail, "_mail's docstring")
        
        