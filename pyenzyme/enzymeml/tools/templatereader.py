# File: templatereader.py
# Project: tools
# Author: Jan Range
# License: BSD-2 clause
# Copyright (c) 2022 Institute of Biochemistry and Technical Biochemistry Stuttgart

import numpy as np
import pandas as pd
import re

from typing import List, Dict

from pyenzyme.enzymeml.core.ontology import DataTypes
from pyenzyme.enzymeml.core.creator import Creator
from pyenzyme.enzymeml.core.vessel import Vessel
from pyenzyme.enzymeml.core.protein import Protein
from pyenzyme.enzymeml.core.reactant import Reactant
from pyenzyme.enzymeml.core.enzymereaction import EnzymeReaction
from pyenzyme.enzymeml.core.measurement import Measurement
from pyenzyme.enzymeml.core.replicate import Replicate


def read_template(path: str, enzmldoc):
    """Reads the EnzymeML spreadsheet template to an EnzymeML document.

    Args:
        path (str): Path to the EnzymeML spreadsheet template.

    Returns:
        EnzymeMLDocument: The resulting EnzymeML document.
    """

    general_info = pd.read_excel(path, sheet_name="General Information", skiprows=1)

    params = dict(
        name=general_info.iloc[0, 1],
        created=str(general_info.iloc[1, 1]),
        doi=None,
        pubmedid=general_info.iloc[3, 1],
        url=general_info.iloc[4, 1],
    )

    enzmldoc = enzmldoc(**params)

    # User information
    user_infos = pd.read_excel(
        path, sheet_name="General Information", skiprows=9
    ).dropna()

    for record in user_infos.to_dict(orient="records"):
        enzmldoc.addCreator(
            Creator(
                family_name=record["Family Name"],
                given_name=record["Given Name"],
                mail=record["Mail"],
            )
        )

    # Vessel
    vessels = pd.read_excel(path, sheet_name="Vessels", skiprows=2)
    instances = get_instances(vessels, Vessel, enzmldoc)

    for instance in instances:
        enzmldoc.addVessel(Vessel(**instance))

    # Proteins
    proteins = pd.read_excel(path, sheet_name="Proteins", skiprows=2)
    instances = get_instances(proteins, Protein, enzmldoc)

    for instance in instances:
        enzmldoc.addProtein(Protein(**instance))

    # Reactants
    reactants = pd.read_excel(path, sheet_name="Reactants", skiprows=2)

    instances = get_instances(reactants, Reactant, enzmldoc)

    for instance in instances:
        enzmldoc.addReactant(Reactant(**instance))

    # Reactions
    reactions = pd.read_excel(path, sheet_name="Reactions", skiprows=2)

    # Merge proteins and modifiers
    nu_mods = [
        merge_protein_modifier(protein, modifier)
        for modifier, protein in zip(
            reactions.Modifiers.values.tolist(), reactions.Proteins.values.tolist()
        )
    ]

    # Replace merged modifiers with modifier tag
    reactions.Modifiers = nu_mods

    instances = get_instances(reactions, EnzymeReaction, enzmldoc)

    for instance in instances:

        # Get Educts, Products and Modifiers to add to the reaction
        educts = parse_reaction_element(instance.get("educts"))
        products = parse_reaction_element(instance.get("products"))
        modifiers = parse_reaction_element(instance.get("modifiers"))

        instance.pop("educts")
        instance.pop("products")
        instance.pop("modifiers")

        # Instantiate Reaction
        reaction = EnzymeReaction(**instance)

        add_instances(reaction.addModifier, modifiers, enzmldoc)
        add_instances(reaction.addEduct, educts, enzmldoc)
        add_instances(reaction.addProduct, products, enzmldoc)

        enzmldoc.addReaction(reaction)

    # Measurements
    data = pd.read_excel(path, sheet_name="Data", skiprows=2)

    # Reduce dataset to experiment IDs
    experiment_ids = set(data["Experiment ID"].dropna())

    for experiment_id in experiment_ids:
        exp_data = data[data["Experiment ID"] == experiment_id]
        exp_data.columns = rename_columns(exp_data)

        # Get split index
        split_index = get_split_index(exp_data)

        measurement = Measurement(name=experiment_id)

        # Get time
        time_values, time_unit = get_time(exp_data, split_index)

        measurement.global_time = time_values
        measurement.global_time_unit = time_unit

        # initialize replicate index
        replicate_index = 0

        for i, row in exp_data.iterrows():

            row_meta = row.iloc[0:split_index].to_dict()
            row_values = row.iloc[split_index::].dropna().values.tolist()

            if "Time" in row_meta["Type"]:
                continue

            protein_name = row_meta["Protein Name"]
            protein_conc = row_meta["Protein Initial concentration"]
            protein_unit = row_meta["Protein Unit"]

            measurement.addData(
                init_conc=protein_conc,
                unit=protein_unit,
                protein_id=enzmldoc.getProtein(protein_name.strip()).id,
            )

            reactant_name = row_meta["Reactant Name"]
            reactant_conc = row_meta["Reactant Initial concentration"]
            reactant_unit = row_meta["Reactant Unit"]
            reactant_id = enzmldoc.getReactant(reactant_name.strip()).id

            # Get the type of the measurement
            type_mapping = {
                "Concentration": DataTypes.CONCENTRATION,
                "Absorption": DataTypes.ABSORPTION,
                "Conversion [%]": DataTypes.CONVERSION,
                "Peak Area": DataTypes.PEAK_AREA,
                "Total concentration after addition": DataTypes.CONCENTRATION,
            }

            if reactant_id not in measurement.species_dict["reactants"]:
                measurement.addData(
                    init_conc=reactant_conc, unit=reactant_unit, reactant_id=reactant_id
                )

            replicates = None
            if row_values:

                if type_mapping[row["Type"]] is DataTypes.CONVERSION:
                    # Convert percent to rational [0,1]
                    row_values = list(map(lambda value: value / 100, row_values))
                    reactant_unit = "dimensionless"
                elif type_mapping[row["Type"]] is DataTypes.PEAK_AREA:
                    # Add dimensionless unit
                    if any(value < 0 for value in row_values):
                        raise ValueError(
                            "Peak area cant be negative. Data might be corrupted"
                        )

                    reactant_unit = "dimensionless"

                # Create Replicate
                replicate = Replicate(
                    id=f"replica_{replicate_index}_{reactant_name}_{experiment_id}",
                    species_id=reactant_id,
                    data_type=type_mapping[row["Type"]],
                    data_unit=reactant_unit,
                    time_unit=time_unit,
                    time=time_values,
                    data=row_values,
                )

                replicate_index += 1

                measurement.addReplicates(replicate, enzmldoc)

        # Finally, add measurement to the document
        enzmldoc.addMeasurement(measurement)

    return enzmldoc


def get_instances(sheet: pd.DataFrame, obj, enzmldoc) -> list:
    mapping = get_template_map(obj)
    instances = extract_values(sheet, mapping)

    return [clean_instance(instance, enzmldoc) for instance in instances]


def get_template_map(obj) -> dict:
    """Extracts the template mappings"""

    return {
        field.field_info.extra.get("template_alias"): name
        for name, field in obj.__fields__.items()
        if field.field_info.extra.get("template_alias")
    }


def extract_values(sheet: pd.DataFrame, mapping: Dict[str, str]) -> list:

    # Get all valid columns
    cols = [col for col in sheet.columns if "Unnamed" not in col]
    sheet = sheet[cols]
    sheet = sheet.replace(r"^\s*$", np.nan, regex=True)
    sheet = sheet.dropna(thresh=len(mapping) - 2)
    records = sheet.to_dict(orient="records")

    return [
        {
            mapping.get(key): item
            for key, item in record.items()
            if item and mapping.get(key) and "nan" != repr(item)
        }
        for record in records
    ]


def clean_instance(instance: dict, enzmldoc) -> dict:
    def get_vessel_name(name: str, enzmldoc):
        return enzmldoc.getVessel(name).id

    def get_constant(constant: str, enzmldoc):
        if constant == "Constant":
            return True
        elif constant == "Not constant":
            return False

    def get_reversible(reversible: str, enzmldoc):
        if reversible == "reversible":
            return True
        elif reversible == "irreversible":
            return False

    def clean_temp_unit(temp_unit: str, enzmldoc):
        return temp_unit.replace("°", "")

    def clean_uniprotid(uniprotid: str, enzmldoc):
        if repr(uniprotid) == "nan":
            return None
        else:
            uniprotid

    mapping = {
        "vessel_id": get_vessel_name,
        "constant": get_constant,
        "temperature_unit": clean_temp_unit,
        "reversible": get_reversible,
        "uniprotid": clean_uniprotid,
    }

    for key, item in instance.items():
        if key in mapping:
            instance[key] = mapping[key](item, enzmldoc)

    return instance


def merge_protein_modifier(protein, modifier):
    proteins = repr(protein).split(",")
    modifier = repr(modifier).split(",")
    entities = proteins + modifier

    return ",".join(
        [entity.replace("'", "").strip() for entity in entities if entity != "nan"]
    )


def rename_columns(columns: List[str]) -> List[str]:
    mapping = {
        "Unnamed: 4": "Protein Initial concentration",
        "Unnamed: 5": "Protein Unit",
        "Unnamed: 7": "Reactant Initial concentration",
        "Unnamed: 8": "Reactant Unit",
        "Protein": "Protein Name",
        "Reactant": "Reactant Name",
    }

    return [mapping[col] if mapping.get(col) else col for col in columns]


def get_split_index(df: pd.DataFrame):
    for index, col in enumerate(df.columns):
        if "Enter data via transpose" in col:
            return index


def get_time(data: pd.DataFrame, split_index):
    for i, (_, row) in enumerate(data.iterrows()):
        if "Time" in row["Type"]:
            time_meta = row.iloc[0:split_index].to_dict()
            time_unit = get_time_unit(time_meta)

            time_values = row.iloc[split_index::].dropna().values

            return time_values.tolist(), time_unit


def get_time_unit(row: dict):

    regex = r"\[([A-Za-z]*)\]"
    regex = re.compile(regex)
    unit = regex.findall(row["Type"])[0]

    return unit


def parse_reaction_element(elements):
    if repr(elements) == "nan":
        return []

    return elements


def add_instances(fun, elements, enzmldoc) -> None:
    all_species = {**enzmldoc.protein_dict, **enzmldoc.reactant_dict}
    for id, species in all_species.items():

        if species.name in elements:
            fun(
                species_id=id,
                stoichiometry=1.0,
                constant=False,
                enzmldoc=enzmldoc,
            )
