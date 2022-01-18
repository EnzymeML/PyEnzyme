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

import json
import os
import pydantic

from typing import Any
from pyDaRUS import EnzymeMl, Citation, Dataset
from pyDaRUS.metadatablocks.enzymeML import Constant
from pyDaRUS.metadatablocks.citation import SubjectEnum


def uploadToDataverse(enzmldoc, dataverse_name: str) -> None:
    """Uploads a givene EnzymeMLDocument object to a dataverse installation.

    It should be noted, that the environment variables 'DATAVERSE_URL' and 'DATAVERSE_API_TOKEN'
    should be given approriately before the upload. If not, tje upload cant be done.

    Args:
        enzmldoc (EnzymeMLDocument): The EnzymeMLDocument to be uploaded.
        dataverse_name (str): Name of the dataverse to be uploaded to.
    """

    # Fill in all the metadatablocks
    enzml_meta = create_enzymeml_metadatablock(enzmldoc)
    citation_meta = create_citation_metadatablock(enzmldoc)

    # Initialize a dataset for the upload
    dataset = Dataset()

    # Add all metadatablocks
    dataset.add_metadatablock(enzml_meta)
    dataset.add_metadatablock(citation_meta)

    # Write EnzymeMLDocument to file
    enzmldoc.toFile(".")

    try:
        dataset.upload(
            dataverse_name=dataverse_name,
            filenames=[f"{enzmldoc.name.replace(' ', '_')}.omex"]
        )
    except Exception as e:
        os.remove(f"{enzmldoc.name.replace(' ', '_')}.omex")
        raise e

    # Remove the unsued EnzymeML document
    os.remove(f"{enzmldoc.name.replace(' ', '_')}.omex")


def create_enzymeml_metadatablock(enzmldoc: "EnzymeMLDocument") -> "EnzymeMl":

    # Initialize the EnzymeML metadatablock
    enzml_meta = EnzymeMl()

    # Vessels
    vessel_mapping = {
        "name": "name",
        "volume": "size",
        "unit": "unit",
        "constant": "constant"
    }

    for vessel in enzmldoc.vessel_dict.values():
        json_data = json.loads(vessel.json())

        # Apply corrections to match controlled vocabs
        json_data["constant"] = Constant.constant.value if json_data["constant"] else Constant.not_constant.value

        add_object(json_data, vessel_mapping, enzml_meta.add_vessels)

    protein_mapping = {
        # "id": "identifier",
        "name": "name",
        "vessel_id": "vessel_reference",
        "init_conc": "initial_concentration",
        "unit": "unit",
        "constant": "constant",
        "sequence": "sequence",
        "organism": "organism",
        "uniprotid": "uniprotid",
        "ecnumber": "ecnumber",
        "ontology": "sbo_term"
    }

    for protein in enzmldoc.protein_dict.values():
        json_data = json.loads(protein.json())

        # Apply corrections to match controlled vocabs
        json_data["constant"] = Constant.constant.value if json_data["constant"] else Constant.not_constant.value

        add_object(json_data, protein_mapping, enzml_meta.add_proteins)

    reactant_mapping = {
        # "id": "identifier",
        "name": "name",
        "vessel_id": "vessel_reference",
        "init_conc": "initial_concentration",
        "unit": "unit",
        "constant": "constant",
        "inchi": "inchicode",
        "smiles": "smilescode",
        "ontology": "sbo_term"
    }

    for reactant in enzmldoc.reactant_dict.values():
        json_data = json.loads(reactant.json())

        # Apply corrections to match controlled vocabs
        json_data["constant"] = Constant.constant.value if json_data["constant"] else Constant.not_constant.value

        add_object(json_data, reactant_mapping, enzml_meta.add_reactants)

    reaction_mapping = {
        "name": "name",
        "temperature": "temperature_value",
        "temperature_unit": "temperature_unit",
        "ph": "ph_value"
    }

    for reaction in enzmldoc.reaction_dict.values():

        params: dict[str, Any] = {
            reaction_mapping.get(key): item
            for key, item in reaction.dict().items()
            if reaction_mapping.get(key) and repr(item) != "nan" and item
        }

        # Apply corrections
        if params.get("temperature_unit"):
            params["temperature_unit"] = "Kelvin" if params["temperature_unit"] == "K" else "Celsius"

        # Extract al elements present in the reaction
        educts = [
            enzmldoc.getAny(element.species_id).name
            for element in reaction.educts
        ]

        products = [
            enzmldoc.getAny(element.species_id).name
            for element in reaction.products
        ]

        modifiers = [
            enzmldoc.getAny(element.species_id).name
            for element in reaction.products
        ]

        # Create corresponding string representations
        params["educts"] = ", ".join(educts)
        params["products"] = ", ".join(products)
        params["modifiers"] = ", ".join(modifiers)
        params["equation"] = " + ".join(educts) + " -> " + " + ".join(products)

        enzml_meta.add_reactions(**params)

        if reaction.model:
            # Report on the model if given
            law_params = kinetic_law_params(reaction)
            enzml_meta.add_kinetic_law(**law_params)

            for param in reaction.model.parameters:
                json_data = json.loads(param.json())

                enzml_meta.add_kinetic_parameters(
                    name=f"{json_data['name']}_{reaction.id}",
                    value=json_data["value"],
                    unit=json_data["unit"],
                    sbo_term=json_data.get("ontology")
                )

    return enzml_meta


def add_object(json_data, mapping, add_fun):

    params = {
        mapping.get(key): item
        for key, item in json_data.items()
        if mapping.get(key) and repr(item) != "nan" and item
    }

    # TODO fix metadatablock to accept other units than MOLAR
    if params.get("unit"):
        params["unit"] = params["unit"].replace("mole / l", "M")

    try:
        # Add infos to metadatablock
        add_fun(**params)
    except pydantic.ValidationError as e:

        # TODO find a better way to handle this error
        for error in e.errors():
            if error["loc"][0] == "unit":
                print(params["name"], params["unit"])
                params.pop("unit")
                add_fun(**params)

                return None

        raise e


def kinetic_law_params(reaction: "EnzymeReaction") -> dict[str, str]:
    """Retrieves the arguments to add a kinetic law to an EnzymeML Metadatablock"""

    kinetic_law_mapping = {
        "name": "name",
        "equation": "kinetic_model"
    }

    # Get the model
    model = reaction.model

    params = {
        kinetic_law_mapping.get(key): item
        for key, item in model.dict().items()
        if kinetic_law_mapping.get(key) and repr(item) != "nan" and item
    }

    params["reaction_reference"] = reaction.id

    return params


def create_citation_metadatablock(enzmldoc: "EnzymeMLDocument"):

    # Initialize the Citation metadatablock
    citation_meta = Citation(
        title=enzmldoc.name,
        subject=[
            SubjectEnum.chemistry,
            SubjectEnum.medicine___health_and__life__sciences
        ]
    )

    # Add author information
    for creator in enzmldoc.creator_dict.values():
        name = f"{creator.given_name} {creator.family_name}"
        citation_meta.add_author(name=name)
        citation_meta.add_contact(name=name, email=creator.mail)

    # Add descripiton
    citation_meta.add_description(
        text=f"EnzymeML document reporting on {enzmldoc.name}"
    )

    return citation_meta
