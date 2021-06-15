'''
File: baseclass.py
Project: core
Author: Jan Range
License: BSD-2 clause
-----
Last Modified: Tuesday June 15th 2021 7:48:31 pm
Modified By: Jan Range (<jan.range@simtech.uni-stuttgart.de>)
-----
Copyright (c) 2021 Institute of Biochemistry and Technical Biochemistry Stuttgart
'''

from pyenzyme.enzymeml.core.functionalities import TypeChecker


class EnzymeMLBase(object):

    def __init__(
        self,
        uri,
        creatorId
    ):
        if creatorId:
            self.setCreatorId(creatorId)
        if uri:
            self.seturi(uri)

    def setURI(self, uri):
        self.__uri = TypeChecker(uri, str)

    def getURI(self):
        return self.__uri

    def delURI(self):
        del self.__uri

    def setCreatorId(self, creatorId, enzmldoc):
        if creatorId in enzmldoc.getCreatorDict().keys():
            self.__creatorId = TypeChecker(creatorId, str)

    def getCreatorId(self):
        return self.__creatorId

    def delCreatorId(self):
        del self.__creatorId
