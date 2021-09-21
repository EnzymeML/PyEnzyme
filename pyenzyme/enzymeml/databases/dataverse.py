'''
File: dataverse.py
Project: core
Author: Jan Range
License: BSD-2 clause
-----
Last Modified: Thursday September 16th 2021 6:43:34 pm
Modified By: Jan Range (<jan.range@simtech.uni-stuttgart.de>)
-----
Copyright (c) 2021 Institute of Biochemistry and Technical Biochemistry Stuttgart
'''

from pyenzyme.enzymeml.databases.dataverseMapping import DataverseMapping
from pyenzyme.enzymeml.core.functionalities import DataverseError, ValidationError
from pyDataverse.models import Datafile, Dataset
from pyDataverse.api import NativeApi

import pyenzyme.enzymeml.core.enzymemldocument as EnzDoc

import json
import os


class DataverseFieldBase(object):
    """This class serves as the basis for dataverse fields."""

    def __init__(self, typeName, multiple, typeClass, value=None):

        self.typeName = typeName
        self.multiple = multiple
        self.typeClass = typeClass
        self.value = value

    def toJSON(self, d=False):

        def transformAttr(self):
            jsonData = dict()
            for key, item in self.__dict__.items():

                if key == "value":

                    try:
                        fields = {
                            typeName: field.toJSON(d=True)
                            for typeName, field in item.items()
                        }

                        jsonData[key] = fields

                    except AttributeError:
                        jsonData[key] = item

                else:
                    jsonData[key] = item

            return jsonData

        if d:
            return transformAttr(self)

        else:
            return json.dumps(
                self,
                default=transformAttr,
                sort_keys=True,
                indent=4
            )


class ParameterSet(object):
    """This class serves as a helper to separate parameters from kineticLaws and to maintain modularity."""

    def __init__(self, name, value, unit):
        self.name = name
        self.value = value
        self.unit = unit

    def toJSON(self, d=False, enzmldoc=None):
        jsonData = dict()
        for key, item in self.__dict__.items():

            if key == "unit":
                jsonData[key] = enzmldoc.getUnitString(item)
            else:
                jsonData[key] = item

        if d:
            return jsonData
        else:
            return json.dumps(jsonData, sort_keys=True, indent=4)


def uploadToDataverse(baseURL, API_Token, dataverseName, filename=None, enzmldoc=None):
    """Uploads an EnzymeML document to Dataverse. Can be done using either a path to upload an existing OMEX archive or directly from an EnzymeMLDocument object. Please note, that when this method is used with an object, the OMEX archive will be written to your current working directory.

    Args:
        baseURL (String): URL to a Dataverse installation
        API_Token (String): API Token given from your Dataverse installation for authentication.
        dataverseName (String): Name of the dataverse to upload the EnzymeML document. You can find the name in the link of your dataverse (e.g. https://dataverse.installation/dataverse/{dataverseName})
        filename (String, optional): Specifies the path to an already existing OMEX archive. Please note, if given, any EnzymeMLDocument in the 'enzmldoc' argument are overriden. Defaults to None.
        enzmldoc (EnzymeMLDocument, optional): EnzymeML document object describing an experiment. Defaults to None.

    Raises:
        AttributeError: Raised when neither a filename nor an EnzymeMLDocument object was provided.
        ValidationError: Raised when the validation fails.
    """

    if filename:
        enzmldoc = EnzDoc.EnzymeMLDocument.fromFile(filename)
    elif enzmldoc:
        enzmldoc.toFile(".", verbose=0)
        filename = f"{enzmldoc.getName().replace(' ', '_')}.omex"
        filename = os.path.join(".", filename)
    else:
        raise AttributeError(
            "Please specify either a path to an EnzymeML document or an EnzymeMLDocument object"
        )

    # Check if the minimal requirement (Dataset authors) is given
    if enzmldoc.hasCreator() is False:
        raise ValidationError(
            "Please provide at least one author for the dataset. Otherwise Dataverse wont accept the dataset. For this, initialize a `Creator` object and add it to the EnzymeMLDocument via enzmldoc.setCreator() method."
        )

    # Initialize pyDataverse API and Dataset
    api = NativeApi(baseURL, API_Token)
    ds = Dataset()
    ds.from_json(enzmldoc.toDataverseJSON())

    # Finally, validate the JSON
    if ds.validate_json():
        response = api.create_dataset(
            dataverseName, enzmldoc.toDataverseJSON()
        )

        if response.json()["status"] == "OK":
            df = Datafile()
            ds_pid = response.json()["data"]["persistentId"]
            df.set({"pid": ds_pid, "filename": filename})

            response = api.upload_datafile(ds_pid, filename, df.json())

        else:
            raise DataverseError(
                f"Your dataset could not be uploaded to the dataverse. Please revisit the error log: \n\n{response.text}"
            )

    else:
        raise ValidationError(
            f"The EnzymeML document for {dataverseName} is invalid. Please revisit the logs that were printed while validation."
        )


def toDataverseJSON(enzmldoc):
    """Generates a Dataverse compatible JSON string to upload an EnzymeMLDocument.

    Returns:
        String: Dataverse compatible JSON string
    """

    vesselCompound = generateCompoundField(
        objects=[enzmldoc.getVessel()],
        className="enzymeMLVessel",
        multiple=True,
        enzmldoc=enzmldoc
    )

    reactantsCompound = generateCompoundField(
        objects=enzmldoc.getReactantList(),
        className="enzymeMLReactant",
        multiple=True,
        enzmldoc=enzmldoc
    )

    proteinsCompound = generateCompoundField(
        objects=enzmldoc.getProteinList(),
        className="enzymeMLProtein",
        multiple=True,
        enzmldoc=enzmldoc
    )

    reactionsCompound = generateCompoundField(
        objects=enzmldoc.getReactionList(),
        className="enzymeMLReaction",
        multiple=True,
        enzmldoc=enzmldoc
    )

    kineticLaws, parameters = __getAllKineticLaws(enzmldoc)

    kineticLawCompound = generateCompoundField(
        objects=kineticLaws,
        className="enzymeMLKineticLaw",
        multiple=True,
        enzmldoc=enzmldoc
    )

    kineticParameterCompound = generateCompoundField(
        objects=parameters,
        className="enzymeMLKineticParameter",
        multiple=True,
        enzmldoc=enzmldoc
    )

    # Summarize all compounds to the EnzymeML Metadatablock
    enzymeMLMetadata = {
        "displayName": "EnzymeML Metadata",
        "fields": [
            vesselCompound,
            reactantsCompound,
            proteinsCompound,
            reactionsCompound,
            kineticLawCompound,
            kineticParameterCompound
        ]
    }

    # Generate citation metadata

    # Title information
    titleField = DataverseFieldBase(
        typeName="title",
        multiple=False,
        typeClass="primitive",
        value=enzmldoc.getName()
    ).toJSON(d=True)

    # Dataset description
    dsDescripitonValueField = DataverseFieldBase(
        typeName="dsDescriptionValue",
        multiple=False,
        typeClass="primitive",
        value=f"EnzymeML document describing {enzmldoc.getName()}"
    ).toJSON(d=True)

    dsDescriptionField = DataverseFieldBase(
        typeName="dsDescription",
        multiple=True,
        typeClass="compound",
        value=[{"dsDescriptionValue": dsDescripitonValueField}]
    ).toJSON(d=True)

    # Subject information
    subject = DataverseFieldBase(
        typeName="subject",
        multiple=True,
        typeClass="controlledVocabulary",
        value=["Chemistry"]
    ).toJSON(d=True)

    # Author information
    creators = list()

    for i, creator in enumerate(enzmldoc.getCreator()):

        nameString = f"{creator.getGname()}, {creator.getFname()}"

        authorName = DataverseFieldBase(
            typeName="authorName",
            multiple=False,
            typeClass="primitive",
            value=nameString
        ).toJSON(d=True)

        creators.append({
            authorName["typeName"]: authorName
        })

        if i == 0:
            # Get contact data
            datasetContactEmail = DataverseFieldBase(
                typeName="datasetContactEmail",
                multiple=False,
                typeClass="primitive",
                value=creator.getMail()
            ).toJSON(d=True)

            datasetContactName = DataverseFieldBase(
                typeName="datasetContactName",
                multiple=False,
                typeClass="primitive",
                value=nameString
            ).toJSON(d=True)

            datasetContactCompound = DataverseFieldBase(
                typeName="datasetContact",
                multiple=True,
                typeClass="compound",
                value=[{
                    field["typeName"]: field
                    for field in
                    [datasetContactEmail, datasetContactName]
                }]
            ).toJSON(d=True)

    authorCompound = DataverseFieldBase(
        typeName="author",
        multiple=True,
        typeClass="compound",
        value=creators
    ).toJSON(d=True)

    # Compose citation metadatablock
    citationMetadata = {
        "displayName": "Citation Metadata",
        "fields": [
            titleField,
            datasetContactCompound,
            dsDescriptionField,
            authorCompound,
            subject
        ]
    }

    # Finally, compose both fields
    dataverseDataset = {"datasetVersion":
                        {
                            "metadataBlocks": {"enzymeML": enzymeMLMetadata, "citation": citationMetadata}
                        }
                        }

    return dataverseDataset


def generateCompoundField(objects, className, enzmldoc, multiple=False):

    # Gather meta data
    typeName = className.split("enzymeML")[-1]

    # generate individual fields
    fields = [
        __populateFields(
            obj.toJSON(d=True, enzmldoc=enzmldoc), typeName, enzmldoc)
        for obj in objects
    ]

    # create the compund field
    compound = DataverseFieldBase(
        typeName=className,
        multiple=multiple,
        typeClass="compound",
        value=fields
    )

    return compound.toJSON(d=True)


def __populateFields(dictionary, className, enzmldoc=None):

    # Initialize data structures
    mapping = DataverseMapping[className]
    fields = dict()

    for key, item in dictionary.items():

        try:
            # Get options form DataverseMapping
            options = mapping[key]

            if isinstance(item, bool) is False and isinstance(item, list) is False:
                # Catch bools --> All other types are handled as strings
                item = str(item)

                if "unit" in key.lower():

                    if "mole / l" in item.lower():
                        item = item.replace("mole / l", "M")
                    elif "K" in item:
                        item = "Kelvin"

                else:
                    item = str(item)

            elif "constant" in key:
                # Match metadatablock
                if item is True:
                    item = "Constant"
                else:
                    item = "Not constant"

            # Generatew field and add to fields dictionary
            field = DataverseFieldBase(**options, value=item)
            fields[field.typeName] = field.toJSON(d=True)

        except KeyError:
            pass

    # Handle Reactions
    if className == "Reaction":
        __reorderReaction(fields, enzmldoc)

    return fields


def __reorderReaction(reactionJSON, enzmldoc):
    """Parses the json representation given by generateCompoundField to match the metadatablock's schema.

    Args:
        reactionJSON (dict): JSON representation of the reaction generated by generateCompoundField
    """

    # Initialize variables
    educts, products = [], []

    keys = {
        "enzymeMLReactionEduct",
        "enzymeMLReactionProduct",
        "enzymeMLReactionModifier"
    }

    for key in keys:
        elements = reactionJSON[key]
        elementString = list()

        for element in elements["value"]:
            speciesName = __getSpeciesName(element["species"], enzmldoc)
            elementString.append(speciesName)

            if "Educt" in key:
                educts.append(
                    f"{element['stoich']} {speciesName}"
                )
            elif "Product" in key:
                products.append(
                    f"{element['stoich']} {speciesName}"
                )

        # Add to JSON data
        reactionJSON[key] = DataverseFieldBase(
            typeName=key,
            multiple=False,
            typeClass="primitive",
            value="; ".join(elementString)
        ).toJSON(d=True)

    # Turn everything to a string and add it to the dictionary
    equationString = " -> ".join([
        " + ".join(educts), " + ".join(products)
    ])

    typeName = "enzymeMLReactionEquation"
    reactionJSON[typeName] = DataverseFieldBase(
        typeName=typeName,
        multiple=False,
        value=equationString,
        typeClass="primitive"
    ).toJSON(d=True)


def __getSpeciesName(id_, enzmldoc):
    try:
        return enzmldoc.getReactant(id_).getName()
    except KeyError:
        return enzmldoc.getProtein(id_).getName()


def __getAllKineticLaws(enzmldoc):
    kineticLaws = list()
    parameters = list()

    for reaction in enzmldoc.getReactionList():
        try:
            model = reaction.getModel()
            model.setReaction(reaction.getId())
            kineticLaws.append(model)

            parameterSets = [
                ParameterSet(
                    name=paramName,
                    value=paramValue,
                    unit=paramUnit
                )
                for paramName, (paramValue, paramUnit) in model.getParameters().items()
            ]

            parameters += parameterSets

        except AttributeError:
            pass

    return kineticLaws, parameters
