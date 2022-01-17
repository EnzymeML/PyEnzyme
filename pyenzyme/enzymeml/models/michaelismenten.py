'''
File: michaelismenten.py
Project: models
Author: Jan Range
License: BSD-2 clause
-----
Last Modified: Wednesday June 23rd 2021 10:30:15 pm
Modified By: Jan Range (<jan.range@simtech.uni-stuttgart.de>)
-----
Copyright (c) 2021 Institute of Biochemistry and Technical Biochemistry Stuttgart
'''

from typing import Any
from pyenzyme.enzymeml.core.ontology import SBOTerm
from pyenzyme.enzymeml.models.kineticmodel import ModelFactory
from pyenzyme.enzymeml.core.exceptions import SpeciesNotFoundError


def MichaelisMenten(
    substrate: str,
    protein: str,
    enzmldoc,
    k_cat: dict[str, Any] = {"ontology": SBOTerm.K_CAT},
    k_m: dict[str, Any] = {"ontology": SBOTerm.K_M},
):
    """Sets up a rate law following the Henri-Michaelis-Menten law.

    Args:
        k_cat_val (float): Numeric value of the estimated k_cat value.
        k_cat_unit (str): Unit string of the estimated k_cat value.
        k_m_val (float): Numeric value of the estimated Km value.
        k_m_unit (str): Unit string of the estimated Km value.
        substrate (str): Reactant ID of the converted substrate.
        protein (str): Protein ID of the catalysing enzyme.
        enzmldoc (EnzymeMLDocument): EnzymeML document against which will be validated in terms of IDs.

    Raises:
        SpeciesNotFoundError: If the substrate hasnt been found in the EnzymeML document.
        SpeciesNotFoundError: If the protein hasnt been found in the EnzymeML document.

    Returns:
        KineticModel: The resulting kinetic model.
    """
    # Check if the given IDs are part of the EnzymeML document already
    if substrate not in enzmldoc.getSpeciesIDs():
        raise SpeciesNotFoundError(
            species_id=substrate,
            enzymeml_part="Reactants/Proteins"
        )

    if protein not in enzmldoc.getSpeciesIDs():
        raise SpeciesNotFoundError(
            species_id=protein,
            enzymeml_part="Reactants/Proteins"
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
        ontology=SBOTerm.MICHAELIS_MENTEN
    )

    return model(protein=protein, substrate=substrate)
