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

from pyenzyme.enzymeml.core.ontology import SBOTerm
from pyenzyme.enzymeml.models.kineticmodel import KineticModel, KineticParameter
from pyenzyme.enzymeml.core.exceptions import SpeciesNotFoundError


def MichaelisMenten(
    kcat_val: float,
    kcat_unit: str,
    km_val: float,
    km_unit: str,
    substrate_id: str,
    protein_id: str,
    enzmldoc
):
    """Sets up a rate law following the Henri-Michaelis-Menten law.

    Args:
        kcat_val (float): Numeric value of the estimated kcat value.
        kcat_unit (str): Unit string of the estimated kcat value.
        km_val (float): Numeric value of the estimated Km value.
        km_unit (str): Unit string of the estimated Km value.
        substrate_id (str): Reactant ID of the converted substrate.
        protein_id (str): Protein ID of the catalysing enzyme.
        enzmldoc (EnzymeMLDocument): EnzymeML document against which will be validated in terms of IDs.

    Raises:
        SpeciesNotFoundError: If the substrate hasnt been found in the EnzymeML document.
        SpeciesNotFoundError: If the protein hasnt been found in the EnzymeML document.

    Returns:
        KineticModel: The resulting kinetic model.
    """
    # Check if the given IDs are part of the EnzymeML document already
    if substrate_id not in enzmldoc.getSpeciesIDs():
        raise SpeciesNotFoundError(
            species_id=substrate_id,
            enzymeml_part="Reactants/Proteins"
        )

    if protein_id not in enzmldoc.getSpeciesIDs():
        raise SpeciesNotFoundError(
            species_id=protein_id,
            enzymeml_part="Reactants/Proteins"
        )

    # Create the corresponding equation
    equation = f"(kcat*{substrate_id}*{protein_id}) / ({substrate_id} + Km)"

    # Create list of parameters
    km_parameter = KineticParameter(
        name="Km",
        value=km_val,
        unit=km_unit,
        ontology=SBOTerm.K_M
    )

    kcat_parameter = KineticParameter(
        name="kcat",
        value=kcat_val,
        unit=kcat_unit,
        ontology=SBOTerm.K_CAT
    )

    return KineticModel(
        name="Henri-Michaelis-Menten rate law",
        equation=equation,
        parameters=[km_parameter, kcat_parameter],
        ontology=SBOTerm.MICHAELIS_MENTEN
    )
