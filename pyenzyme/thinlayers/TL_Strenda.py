# File: TL_Strenda.py
# Project: ThinLayers
# Author: Jan Range
# License: BSD-2 clause
# Copyright (c) 2022 Institute of Biochemistry and Technical Biochemistry Stuttgart

import xmltodict
import json
import itertools
import numpy as np

from typing import Dict, List, Tuple, Optional

from pyenzyme.enzymeml.core.enzymemldocument import EnzymeMLDocument
from pyenzyme.enzymeml.core.measurement import Measurement
from pyenzyme.enzymeml.core.reactant import Reactant
from pyenzyme.enzymeml.core.protein import Protein
from pyenzyme.enzymeml.core.enzymereaction import EnzymeReaction
from pyenzyme.enzymeml.core.vessel import Vessel
from pyenzyme.enzymeml.models.michaelismenten import MichaelisMentenKCat


class ThinLayerStrendaML(object):

    """Thin Layer implementation to convert an EnzymeML document into a StrendaML document."""

    @classmethod
    def toEnzymeML(cls, path: str, out_dir: str):
        """Reads a STRENDA-DB XML entry and processes it to an EnzymeML document.

        Args:
            path (str): Path to the STRENDA-DB XML file.
            out_dir (str): Directory to which the resulting EnzymeML file will be written.
        """

        # Initialize Thin layer
        cls = cls()

        # Read the STRENDA ML file
        metadata = cls._read_strendaml(path)
        cls.dataset = metadata["datasets"]["dataset"]
        assay_conditions = cls.dataset["assayConditions"]

        # Initialize the ENzymeML document
        cls.enzmldoc = EnzymeMLDocument(
            name=metadata.get("strendaId"),
            doi=metadata.get("doi"),
        )

        # Set up a playeholder vessel
        vessel = Vessel(name="Vessel")
        cls.vessel_id = cls.enzmldoc.addVessel(vessel)

        # Get the reaction first and build it while parsing species
        cls._setup_reaction()

        # Get small compounds and build reaction
        small_compounds = assay_conditions["smallCompound"]
        init_conc, reactant_ref = cls._parse_small_compounds(small_compounds)

        # Get the protein
        protein = metadata["protein"]
        cls._parse_protein(protein)

        # Get the Michaelis-Menten-Model
        cls._get_kinetic_model(reactant_ref)

        # Use the initial concentrations to construct measurement setups
        cls._setup_measurements(init_conc)

        # Finally, add the reaction to the document
        cls.enzmldoc.addReaction(cls.reaction)

        cls.enzmldoc.toFile(out_dir)

    def _read_strendaml(self, path: str):
        """Reads and extracts the necessary data for the thin layer"""

        # Parse XML string and clean faulty line
        xml_string = open(path).read()
        xml_string = xml_string.replace(
            '<sequenceModifiations value="yes"/>', '<sequenceModifiations value="yes">'
        )

        # Parse XML to JSON and dict
        dict_data = xmltodict.parse(xml_string)
        json_string = json.dumps(dict_data)

        return json.loads(json_string.replace("@", ""))["experiment"]

    def _setup_reaction(self):
        """Sets up a reaction objectm which will later be used to specify the equation and adds it."""

        # Get the assay conditions, if given
        ph, _ = self._get_assay_conditions("pH", self.dataset)
        temp_val, temp_unit = self._get_assay_conditions("temperature", self.dataset)

        self.reaction = EnzymeReaction(
            name=self.dataset.get("name"),
            reversible=False,
            temperature=temp_val,
            temperature_unit=temp_unit,
            ph=ph,
        )

    def _get_assay_conditions(
        self, key: str, dataset: dict
    ) -> Tuple[Optional[float], Optional[str]]:
        """Returns miscellaneous parameters from the 'value' element found in the assayConditions."""

        for obj in dataset["assayConditions"]["value"]:
            if obj["name"] == key:
                return (obj.get("value"), obj.get("unit"))

        return None, None

    def _parse_small_compounds(self, small_compounds: List[dict]):
        """Parses small compounds to Reactant objects"""

        # Keep track of range measurements and the references
        initial_concentrations = []
        reactant_ref = {}

        # Keep a mapping for the different roles to be added to the reaction
        role_mapping = {
            "Substrate": self.reaction.addEduct,
            "Product": self.reaction.addProduct,
        }

        for small_compound in small_compounds:

            # Create Reactant and add it to the document
            reactant_id = self.enzmldoc.addReactant(
                Reactant(
                    name=small_compound.get("iupac"),
                    smiles=small_compound.get("smiles"),
                    inchi=small_compound.get("inchi"),
                    vessel_id=self.vessel_id,
                )
            )

            # Store substance ID
            reactant_reference = small_compound["refId"]
            reactant_ref[reactant_reference] = reactant_id

            # Add it to the reaction
            role = small_compound["role"]
            stoichiometry = float(small_compound["stoichiometry"])
            role_mapping[role](
                species_id=reactant_id,
                stoichiometry=stoichiometry,
                enzmldoc=self.enzmldoc,
            )

            init_conc = small_compound["value"]
            unit = init_conc["unit"].replace("micro", "u")

            if init_conc["type"] == "Concentration":
                value = float(init_conc["value"])
                initial_concentrations.append([(reactant_id, value, unit)])

            elif init_conc["type"] == "ConcentrationRange":
                start_value = float(init_conc["startValue"])
                end_value = float(init_conc["endValue"]) + 0.1
                val_range = np.linspace(start_value, end_value, 10)

                initial_concentrations.append(
                    [(reactant_id, round(val, 4), unit) for val in val_range if val > 0]
                )

        return initial_concentrations, reactant_ref

    def _parse_protein(self, protein: dict):

        # Get and clean some parameters
        sequence = protein.get("originalSequence")
        uniprotid = protein.get("uniprotidKbAC")

        if sequence == "null":
            sequence = None
        if uniprotid == "N.A.":
            uniprotid = None

        self.protein_id = self.enzmldoc.addProtein(
            Protein(
                name=protein.get("name"),
                vessel_id="v0",
                organism=protein.get("organism"),
                sequence=sequence,
                organism_tax_id=protein.get("texonId"),
                uniprotid=uniprotid,
            )
        )

        self.reaction.addModifier(
            species_id=self.protein_id,
            stoichiometry=1.0,
            constant=True,
            enzmldoc=self.enzmldoc,
        )

    def _setup_measurements(self, init_conc: List[Tuple[str, float, str]]):
        """Sets up individual measurements by permuting given initial concentrations, if multiples of"""

        # Permute all initial concentrations
        for index, init_conc_set in enumerate(itertools.product(*init_conc)):

            # Initialize measurement
            measurement = Measurement(name=f"measurement_{index+1}")

            # Add protein to measurement
            protein_conc, protein_unit = self._get_assay_conditions(
                "enzymeConcentration", self.dataset
            )

            measurement.addData(
                protein_id="p0",
                init_conc=protein_conc,
                unit=protein_unit.replace("micro", "u"),
            )

            for species_id, value, unit in init_conc_set:

                species = self.enzmldoc.getAny(species_id)
                reactant_id, protein_id = None, None

                if isinstance(species, Protein):
                    protein_id = species_id
                elif isinstance(species, Reactant):
                    reactant_id = species_id

                # Add the data to the measurement
                measurement.addData(
                    unit=unit,
                    init_conc=value,
                    reactant_id=reactant_id,
                    protein_id=protein_id,
                )

            # Finally, add the measurement to the document
            self.enzmldoc.addMeasurement(measurement)

    def _get_kinetic_model(self, reactant_ref: Dict[str, str]):
        """Extracts the kinetic model from the dataset"""

        # Get parameters and species ID from data structure
        result_set = self.dataset["resultSet"]["kineticParameter"]
        species_id = reactant_ref[result_set.get("substanceId")]
        parameters = result_set["value"]

        for parameter in parameters:
            if parameter["name"] == "kcat":
                kcat = {"unit": "1 / s", "value": float(parameter["value"])}
            elif parameter["name"] == "km":
                km = {
                    "unit": parameter["unit"].replace("micro", "u"),
                    "value": float(parameter["value"]),
                }

        # Create the model and add it to the reaction
        model = MichaelisMentenKCat(
            substrate=species_id,
            protein="p0",
            enzmldoc=self.enzmldoc,
            k_m=km,
            k_cat=kcat,
        )

        self.reaction.setModel(model, self.enzmldoc)
