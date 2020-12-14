'''
File: /creator.py
Project: EnzymeML
Created Date: November 10th 2020
Author: Jan Range
-----
Last Modified: Friday December 11th 2020 4:05:57 pm
Modified By: the developer formerly known as Jan Range at <range.jan@web.de>
-----
Copyright (c) 2020 Institute Of Biochemistry and Technical Biochemistry Stuttgart
'''

from pyenzyme.enzymeml.core.functionalities import TypeChecker
import json

class Creator(object):

    def __init__(self, family_name, given_name, mail):
        """Author information class. 

        Args:
            family_name (string): Family name of author
            given_name (string): Given name of author
            mail (string): E-Mail of author
        """
        
        self.setFname(family_name)
        self.setGname(given_name)
        self.setMail(mail)

    def toJSON(self, d=False, enzmldoc=False):
        """Turns object to either JSON formatted string or dictionary.

        Args:
            d (bool, optional): Returns dictionary instead of JSON string. Defaults to False.
            enzmldoc (bool, optional): Used to convert unit/species IDs to Name/JSON. Defaults to False.

        Returns:
            string: JSON-formatted string
        """
        
        f = lambda o: { key.split('__')[-1]: item for key, item in o.__dict__.items()}
        
        if d: return f(self)
        
        return json.dumps(
            self, 
            default=f, 
            indent=4
            )
    
    def __str__(self):
        """Returns Creator object as JSON-formatted string
        
        Returns:
            string: JSON-formatted string
        """
        return self.toJSON()

    def getFname(self):
        """
        
        Returns:
            string: Author family name
        """
        return self.__fname


    def getGname(self):
        """

        Returns:
            string: Author given name
        """
        return self.__gname


    def getMail(self):
        """

        Returns:
            string: Author E-Mail
        """
        return self.__mail

    def setFname(self, family_name):
        """Sets family name

        Args:
            family_name (string): Authors family name
        """
        self.__fname = TypeChecker(family_name, str)


    def setGname(self, given_name):
        """Sets given name

        Args:
            given_name (string): Authors given name
        """
        self.__gname = TypeChecker(given_name, str)


    def setMail(self, mail):
        """Sets E-Mail

        Args:
            mail (string): Authors E-Mail
        """
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
        
        