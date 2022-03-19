# File: michaelismenten.py
# Project: models
# Author: Jan Range
# License: BSD-2 clause
# Copyright (c) 2021 Institute of Biochemistry and Technical Biochemistry Stuttgart

from typing import Any, Dict
from pyenzyme.enzymeml.core.ontology import SBOTerm
from pyenzyme.enzymeml.models.kineticmodel import ModelFactory
from pyenzyme.enzymeml.core.exceptions import SpeciesNotFoundError


def MichaelisMentenKCat(
    substrate: str,
    protein: str,
    enzmldoc,
    k_cat: Dict[str, Any] = {"ontology": SBOTerm.K_CAT},
    k_m: Dict[str, Any] = {"ontology": SBOTerm.K_M},
):
    """Sets up a rate law following the Henri-Michaelis-Menten law.

    v = k_cat * protein * substrate / (k_m + substrate)

    Args:
        substrate (str): Identifier or name of the substrate.
        protein (str): Identifier or name of the protein.
        enzmldoc ([type]): EnzymeML document to which the model will be adopted.
        k_cat (Dict[str, Any], optional): Dictionary for parameter config. See KineticParameter class for details. Defaults to {"ontology": SBOTerm.K_CAT}.
        k_m (Dict[str, Any], optional): Dictionary for parameter config. See KineticParameter class for details. Defaults to {"ontology": SBOTerm.K_CAT}.

    Returns:
        KineticModel: Michaelis-Menten model in K_cat form with the specified parameters.
    """
    # Check if the given IDs are part of the EnzymeML document already
    if substrate not in enzmldoc.getSpeciesIDs():
        raise SpeciesNotFoundError(
            species_id=substrate, enzymeml_part="Reactants/Proteins"
        )

    if protein not in enzmldoc.getSpeciesIDs():
        raise SpeciesNotFoundError(
            species_id=protein, enzymeml_part="Reactants/Proteins"
        )

    # Check if ontologies are added, if not add them
    if k_m.get("ontology") is None:
        k_m["ontology"] = SBOTerm.K_M

    if k_cat.get("ontology") is None:
        k_cat["ontology"] = SBOTerm.K_CAT

    # Create the model using a factory
    model = ModelFactory(
        name="Michaelis-Menten Rate Law",
        equation="k_cat * protein * substrate / (k_m + substrate)",
        k_cat=k_cat,
        k_m=k_m,
        ontology=SBOTerm.MICHAELIS_MENTEN,
    )

    return model(protein=protein, substrate=substrate)


def MichaelisMentenVMax(
    substrate: str,
    enzmldoc,
    vmax: Dict[str, Any] = {"ontology": SBOTerm.V_MAX},
    k_m: Dict[str, Any] = {"ontology": SBOTerm.K_M},
):
    """Sets up a rate law following the Henri-Michaelis-Menten law.

    v = vmax * substrate / (k_m + substrate)

    Args:
        substrate (str): Identifier or name of the substrate.
        protein (str): Identifier or name of the protein.
        enzmldoc ([type]): EnzymeML document to which the model will be adopted.
        k_cat (Dict[str, Any], optional): Dictionary for parameter config. See KineticParameter class for details. Defaults to {"ontology": SBOTerm.K_CAT}.
        k_m (Dict[str, Any], optional): Dictionary for parameter config. See KineticParameter class for details. Defaults to {"ontology": SBOTerm.K_CAT}.

    Returns:
        KineticModel: Michaelis-Menten model in K_cat form with the specified parameters.
    """

    # Check if the given IDs are part of the EnzymeML document already
    if substrate not in enzmldoc.getSpeciesIDs():
        raise SpeciesNotFoundError(
            species_id=substrate, enzymeml_part="Reactants/Proteins"
        )

    # Check if ontologies are added, if not add them
    if k_m.get("ontology") is None:
        k_m["ontology"] = SBOTerm.K_M

    if vmax.get("ontology") is None:
        vmax["ontology"] = SBOTerm.V_MAX

    # Create the model using a factory
    model = ModelFactory(
        name="Michaelis-Menten Rate Law",
        equation="vmax * substrate / (k_m + substrate)",
        vmax=vmax,
        k_m=k_m,
        ontology=SBOTerm.MICHAELIS_MENTEN,
    )

    return model(substrate=substrate)
