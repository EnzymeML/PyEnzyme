'''
File: creator.py
Project: core
Author: Jan Range
License: BSD-2 clause
-----
Last Modified: Tuesday June 15th 2021 6:28:16 pm
Modified By: Jan Range (<jan.range@simtech.uni-stuttgart.de>)
-----
Copyright (c) 2021 Institute of Biochemistry and Technical Biochemistry Stuttgart
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
            d (bool, optional): Returns dictionary. Defaults to False.
            enzmldoc (bool, optional): Used to convert unit/species IDs
                                       to Name/JSON. Defaults to False.

        Returns:
            string: JSON-formatted string
        """

        def transformAttr(classDict):
            return {
                    key.split('__')[-1]: item
                    for key, item in classDict.items()
                    }

        if d:
            return transformAttr(self.__dict__)

        return json.dumps(
            self,
            default=transformAttr,
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
        return self.__family_name

    def getGname(self):
        """
        Returns:
            string: Author given name
        """
        return self.__given_name

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
        self.__family_name = TypeChecker(family_name, str)

    def setGname(self, given_name):
        """Sets given name

        Args:
            given_name (string): Authors given name
        """
        self.__given_name = TypeChecker(given_name, str)

    def setMail(self, mail):
        """Sets E-Mail

        Args:
            mail (string): Authors E-Mail
        """
        self.__mail = TypeChecker(mail, str)

    def delFname(self):
        del self.__family_name

    def delGname(self):
        del self.__given_name

    def delMail(self):
        del self.__mail

    _fname = property(getFname, setFname, delFname, "_fname's docstring")
    _gname = property(getGname, setGname, delGname, "_gname's docstring")
    _mail = property(getMail, setMail, delMail, "_mail's docstring")
