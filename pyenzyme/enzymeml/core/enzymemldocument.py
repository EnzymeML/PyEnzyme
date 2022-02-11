'''
File: enzymemldocument.py
Project: core
Author: Jan Range
License: BSD-2 clause
-----
Last Modified: Thursday July 15th 2021 1:00:05 am
Modified By: Jan Range (<jan.range@simtech.uni-stuttgart.de>)
-----
Copyright (c) 2021 Institute of Biochemistry and Technical Biochemistry Stuttgart
'''

import os
import re
import ast
import json
import yaml
import logging
import pandas as pd
import seaborn as sns

from pydantic import Field, validator, validate_arguments
from typing import TYPE_CHECKING, Optional, Union
from texttable import Texttable
from dataclasses import dataclass
from io import StringIO

from pyenzyme.enzymeml.core.enzymemlbase import EnzymeMLBase
from pyenzyme.enzymeml.core.abstract_classes import AbstractSpecies

from pyenzyme.enzymeml.core.reactant import Reactant
from pyenzyme.enzymeml.core.creator import Creator
from pyenzyme.enzymeml.core.protein import Protein
from pyenzyme.enzymeml.core.complex import Complex
from pyenzyme.enzymeml.core.vessel import Vessel
from pyenzyme.enzymeml.core.unitdef import UnitDef
from pyenzyme.enzymeml.core.measurement import Measurement
from pyenzyme.enzymeml.core.measurementData import MeasurementData
from pyenzyme.enzymeml.core.enzymereaction import EnzymeReaction
from pyenzyme.enzymeml.models.kineticmodel import KineticParameter
from pyenzyme.enzymeml.tools.unitcreator import UnitCreator
from pyenzyme.enzymeml.tools.enzymemlwriter import EnzymeMLWriter
from pyenzyme.enzymeml.tools.templatereader import read_template
from pyenzyme.enzymeml.databases.dataverse import uploadToDataverse

from pyenzyme.enzymeml.core.ontology import EnzymeMLPart, SBOTerm
from pyenzyme.utils.log import setup_custom_logger, log_object
from pyenzyme.enzymeml.core.exceptions import SpeciesNotFoundError
from pyenzyme.enzymeml.core.utils import (
    type_checking,
    deprecated_getter
)


if TYPE_CHECKING:  # pragma: no cover
    static_check_init_args = dataclass
else:
    static_check_init_args = type_checking

# Initialize the logger
logger = logging.getLogger("pyenzyme")


@static_check_init_args
class EnzymeMLDocument(EnzymeMLBase):

    name: str = Field(
        ...,
        description="Title of the EnzymeML Document.",
    )

    level: int = Field(
        3,
        description="SBML evel of the EnzymeML XML.",
        inclusiveMinimum=1,
        exclusiveMaximum=3
    )

    version: str = Field(
        2,
        description="SBML version of the EnzymeML XML.",
    )

    pubmedid: Optional[str] = Field(
        None,
        description="Pubmed ID reference.",
    )

    url: Optional[str] = Field(
        None,
        description="Arbitrary type of URL that is related to the EnzymeML document.",
    )

    doi: Optional[str] = Field(
        None,
        description="Digital Object Identifier of the referenced publication or the EnzymeML document.",
    )

    created: Optional[str] = Field(
        None,
        description="Date the EnzymeML document was created.",
    )

    modified: Optional[str] = Field(
        None,
        description="Date the EnzymeML document was modified.",
    )

    creator_dict: dict[str, Creator] = Field(
        alias="creators",
        default_factory=dict,
        description="Dictionary mapping from creator IDs to creator describing objects.",
    )

    vessel_dict: dict[str, Vessel] = Field(
        alias="vessels",
        default_factory=dict,
        description="Dictionary mapping from vessel IDs to vessel describing objects."
    )

    protein_dict: dict[str, Protein] = Field(
        alias="proteins",
        default_factory=dict,
        description="Dictionary mapping from protein IDs to protein describing objects.",
    )

    complex_dict: dict[str, Complex] = Field(
        alias="complexes",
        default_factory=dict,
        description="Dictionary mapping from complex IDs to complex describing objects.",
    )

    reactant_dict: dict[str, Reactant] = Field(
        alias="reactants",
        default_factory=dict,
        description="Dictionary mapping from reactant IDs to reactant describing objects.",
    )

    reaction_dict: dict[str, EnzymeReaction] = Field(
        alias="reactions",
        default_factory=dict,
        description="Dictionary mapping from reaction IDs to reaction describing objects.",
    )

    unit_dict: dict[str, UnitDef] = Field(
        alias="units",
        default_factory=dict,
        description="Dictionary mapping from unit IDs to unit describing objects.",
    )

    measurement_dict: dict[str, Measurement] = Field(
        alias="measurements",
        default_factory=dict,
        description="Dictionary mapping from measurement IDs to measurement describing objects.",
    )

    file_dict: dict[str, dict] = Field(
        alias="files",
        default_factory=dict,
        description="Dictionary mapping from protein IDs to protein describing objects.",
    )

    log: str = Field(
        default="",
    )

    # ! Validators
    @validator("log")
    def start_logger(cls, logs: str, values: dict):
        """Starts a logger instance for the document"""

        # Initialite the log stream
        log_stream = StringIO()
        log_stream.write(logs)

        # Initialize the global logger
        logger = setup_custom_logger("pyenzyme", log_stream)

        return log_stream

    @validator("pubmedid")
    def add_identifier(cls, pubmedid: Optional[str]):
        """Adds an identifiers.org link in front of the pubmed ID if not given"""

        if pubmedid is None:
            return pubmedid
        elif pubmedid.startswith("https://identifiers.org/pubmed:"):
            return pubmedid
        else:
            return "https://identifiers.org/pubmed:" + pubmedid

    # ! Imports and exports
    @classmethod
    def fromTemplate(cls, path: str):
        """Reads an EnzymeML spreadsheet template to an EnzymeMLDocument object.

        Args:
            path (str): Path to the EnzymeML spreadsheet template.

        Returns:
            EnzymeMLDocument: Resulting EnzymeML document.
        """

        return read_template(path, cls)

    @staticmethod
    def fromFile(path: str):
        """Initializes an EnzymeMLDocument from an OMEX container."

        Args:
            path (Path): Path to the OMEX container.

        Returns:
            EnzymeMLDocument: The intialized EnzymeML document.
        """

        from pyenzyme.enzymeml.tools.enzymemlreader import EnzymeMLReader

        try:
            return EnzymeMLReader().readFromFile(path)
        except AttributeError:
            raise TypeError(
                f"{path} is not a valid OMEX archive."
            )

    @classmethod
    def fromJSON(cls, json_string: str):

        # First, use PyDantic to get a raw model
        enzmldoc = cls.parse_obj(json.loads(json_string))

        # Recreate to get unitDefs and logs
        nu_enzmldoc = cls(
            name=enzmldoc.name,
            level=enzmldoc.level,
            version=enzmldoc.version,
            pubmedid=enzmldoc.pubmedid,
            url=enzmldoc.url,
            doi=enzmldoc.doi,
            created=enzmldoc.created,
            modified=enzmldoc.modified
        )

        # Creators
        for creator in enzmldoc.creator_dict.values():
            nu_enzmldoc.addCreator(creator)

        # Vessels
        for vessel in enzmldoc.vessel_dict.values():
            nu_enzmldoc.addVessel(vessel)

        # Proteins
        for protein in enzmldoc.protein_dict.values():
            nu_enzmldoc.addProtein(protein)

        # Reactants
        for reactant in enzmldoc.reactant_dict.values():
            nu_enzmldoc.addReactant(reactant)

        # Complexes
        for complex in enzmldoc.complex_dict.values():
            nu_enzmldoc._add_complex(complex)

        # Reactions
        for reaction in enzmldoc.reaction_dict.values():
            nu_enzmldoc.addReaction(reaction)

        # Measurements
        for measurement in enzmldoc.measurement_dict.values():
            nu_measurement = Measurement(
                name=measurement.name,
                temperature=measurement.temperature,
                temperature_unit=measurement.temperature_unit,
                ph=measurement.ph,
                global_time_unit=measurement.global_time_unit
            )

            cls._parse_measurement_data(measurement, 'proteins',
                                        nu_measurement, nu_enzmldoc)
            cls._parse_measurement_data(measurement, 'reactants',
                                        nu_measurement, nu_enzmldoc)

            nu_enzmldoc.addMeasurement(nu_measurement)

        return nu_enzmldoc

    @staticmethod
    def _parse_measurement_data(measurement, key, nu_measurement, enzmldoc):
        """Parses measurement data for the fromJSON method"""

        for measurement_data in measurement.species_dict[key].values():
            nu_measurement.addData(
                init_conc=measurement_data.init_conc,
                unit=measurement_data.unit,
                protein_id=measurement_data.protein_id,
                reactant_id=measurement_data.reactant_id
            )

            nu_measurement.addReplicates(
                measurement_data.replicates, enzmldoc=enzmldoc
            )

    def toFile(self, path: str, name: Optional[str] = None):
        """Saves an EnzymeML document to an OMEX container at the specified path

        Args:
            path (Path): Path where the document should be saved.
            verbose (PositiveInt, optional): Level of verbosity, in order to print a message and the resulting path. Defaults to 1.
        """

        EnzymeMLWriter().toFile(self, path, name)

    def toXMLString(self):
        """Generates an EnzymeML XML string"""

        return EnzymeMLWriter().toXMLString(self)

    @validate_arguments
    def uploadToDataverse(
        self,
        dataverse_name: str,
        base_url: Optional[str] = None,
        api_token: Optional[str] = None
    ):
        """Uploads an EnzymeML document to a Dataverse installation of choice.

        It should be noted, that the environment variables 'DATAVERSE_URL' and 'DATAVERSE_API_TOKEN'
        should be given approriately before the upload. If not, tje upload cant be done.

        Args:
            dataverse_name (str): Name of the dataverse to upload the EnzymeML document. You can find the name in the link of your dataverse (e.g. https://dataverse.installation/dataverse/{dataverseName})
            base_url (str): Base URL of the dataverse to upload. Defaults to None. If None the URL will be drawn from env vars.
            api_token (str): API Token of the dataverse to upload. Defaults to None. If None the API Token will be drawn from env vars.

        """
        uploadToDataverse(
            enzmldoc=self,
            dataverse_name=dataverse_name,
            base_url=base_url,
            api_token=api_token
        )

    # ! Utility methods
    def visualize(
        self,
        measurement_ids: list[str] = ["all"],
        use_names: bool = False,
        sharey: bool = True,
        col_wrap: int = 4,
        **kwargs
    ) -> sns.axisgrid.FacetGrid:
        """Visualizes eitehr all or selected measurements found in the EnzymeML document.

        In order to use this method correctly, make sure to pass nothing to 'measurement_ids' when all meassurements
        should be visualised. Otherwise pass a list or string for multiple or single measurements respectively.

        Args:
            measurement_ids (list[str], optional): Measurements that should be visualized. Defaults to ["all"].
            use_names (bool, optional): Whether legend and titles should be based on names or IDs. Defaults to True.
            sharey (bool, optional): Whether individual plots should share the y-axis. Defaults to True.

        Returns:
            sns.axisgrid.FacetGrid: Seaborn plot object which can be further customized.
        """

        if isinstance(measurement_ids, str):
            measurement_ids = [measurement_ids]

        # First export all the experimental data
        data = self.exportMeasurementData()

        # Reformat the dataframe for a FacetGrid plot
        df_plot = []
        for measurement_id, measurement in data.items():

            if measurement_id not in measurement_ids and measurement_ids != ["all"]:
                # Drop discarded measurements
                continue

            if use_names:
                # Turn ID to name if specified
                measurement_id = self.measurement_dict[measurement_id].name

            # Get the dataframe from the data export
            exp_data = measurement["data"]

            # Rename to names if specified
            columns = []
            for column in exp_data.columns:
                if use_names and column != "time":
                    columns.append(self.getAny(column).name)
                else:
                    columns.append(column)

            # Reset columns
            exp_data.columns = columns

            # Reduce DataFrame to three columns to hue indicidual species
            exp_data = pd.melt(exp_data, id_vars=["time"], var_name="species")
            exp_data["measurement"] = [measurement_id] * exp_data.shape[0]

            df_plot.append(exp_data)

        # Finally, concatenate all indivdidual datasets
        df_plot = pd.concat(df_plot)

        # Set up the FacetGrid plot
        g = sns.FacetGrid(
            df_plot, col="measurement", hue="species",
            col_wrap=col_wrap, sharey=sharey, legend_out=True,
            ** kwargs
        )

        g.map(sns.lineplot, "time", "value")
        g.map(sns.scatterplot, "time", "value")
        g.add_legend(loc='upper right', bbox_to_anchor=(
            0.5, -0.01), fancybox=True, shadow=True, ncol=2)

        return g

    def unifyMeasurementUnits(
        self,
        kind: str,
        scale: int,
        measurement_ids: Union[str, list[str]] = "all"
    ) -> None:
        """Rescales and unifies the units of either all measurements or those that are provided to the given kind and scale.

        Args:
            kind (str): The unit kind from which to rescale. Currently supported: 'mole', 'gram', 'litre'.
            scale (int): Decade scale to which the values will be rescaled.
            measurement_ids (Union[str, list[str]], optional): Measurements that will be rescaled. Defaults to "all".
        """

        # Transform single strings to list
        if isinstance(measurement_ids, str):
            measurement_ids = [measurement_ids]

        for measurement_id, measurement in self.measurement_dict.items():
            if measurement_id in measurement_ids or measurement_ids == ["all"]:
                measurement.unifyUnits(kind=kind, scale=scale, enzmldoc=self)

    def exportMeasurementData(
        self,
        measurement_ids: Union[str, list[str]] = "all",
        species_ids: Union[str, list[str]] = "all",
        proteins: bool = False,
        reactants: bool = True,
    ) -> dict[str, dict[str, Union[tuple, pd.DataFrame]]]:
        """Exports either all replicates present in any measurement or the ones specified via 'species_ids' or 'measurement_ids'

        Args:
            measurement_ids (Union[str, list[str]], optional): The measurements from which to export the data. Defaults to "all".
            species_ids (Union[str, list[str]], optional): The species from which to export the data. Defaults to "all".

        Returns:
            dict[str, dict[str, Union[tuple, pd.DataFrame]]]: The data corresponding to the specified options. The dictionary will still distinguish between meassuremnts.
        """

        if isinstance(measurement_ids, str):
            measurement_ids = [measurement_ids]
        if isinstance(species_ids, str):
            species_ids = [species_ids]

        # Initialize return list
        replicate_data = {}

        for measurement_id, measurement in self.measurement_dict.items():
            if measurement_id in measurement_ids or measurement_ids == ["all"]:
                data = measurement.exportData(
                    species_ids=species_ids
                )

                # Initialize the data dict that will be returned
                measurement_data = {}

                if reactants:
                    measurement_data.update(data["reactants"])
                if proteins:
                    measurement_data.update(data["proteins"])

                if measurement_data["data"] is not None:
                    replicate_data[measurement_id] = measurement_data

        return replicate_data

    @ staticmethod
    def _generateID(prefix: str, dictionary: dict) -> str:
        """Generates IDs complying to the [s|p|r|m|u|c]?[digit]+ schema.

        Args:
            prefix (str): Character denoting the type of species (p: Protein, s: Reactant, u: UnitDef, r: EnzymeReaction, m: Measurement, c: concentration).
            dictionary (dict): The dictionary from which the ID is generated and used to determine the number.

        Returns:
            str: Unique internal identifier.
        """

        if dictionary.keys():
            # fetch all keys and sort them
            number = int(
                max(list(dictionary.keys()), key=lambda id: int(id[1::]))[1::]
            )
            return prefix + str(number + 1)

        return prefix + str(0)

    def validateEnzymeML(self) -> None:
        # TODO rework validation
        raise NotImplementedError(
            "Function not refactored yet."
        )

    def __repr__(self) -> str:
        """
        Magic function return pretty string describing the object.

        Returns:
            string: Beautified summarization of object
        """

        return self.printDocument(stdout=False)

    def printDocument(self, measurements: bool = False, units: bool = False, stdout: bool = True) -> Optional[str]:
        """Prints the document's content"""

        fin_string: list[str]

        def generate_lines(dictionary: dict) -> None:
            """Breaks up a dictionary and generates a human readible line."""
            for element_id, element in dictionary.items():
                fin_string.append(
                    f"\tID: {element_id} \t Name: {element.name}")

        fin_string = [self.name]

        if units:
            fin_string.append('>>> Units')
            generate_lines(self.unit_dict)

        fin_string.append('>>> Reactants')
        generate_lines(self.reactant_dict)

        fin_string.append('>>> Proteins')
        generate_lines(self.protein_dict)

        fin_string.append('>>> Complexes')
        generate_lines(self.complex_dict)

        fin_string.append('>>> Reactions')
        generate_lines(self.reaction_dict)

        if measurements:
            fin_string.append('>>> Measurements')
            fin_string.append(self.printMeasurements())

        output = "\n".join(fin_string)

        if stdout:
            print(output)
        else:
            return output

    def printMeasurements(self) -> str:
        """Prints all measurements as a human readable table"""

        table = Texttable()
        table.set_deco(Texttable.HEADER)
        table.set_cols_align(["l", "l", "l", "l"])

        # Initialize rows
        rows = [["ID", "Species", "Conc", "Unit"]]

        # Generate and append rows
        for measurement_id, measurement in self.measurement_dict.items():

            speciesDict = measurement.species_dict
            proteins = speciesDict['proteins']
            reactants = speciesDict['reactants']

            # succesively add rows with schema
            # [ measID, speciesID, initConc, unit ]

            for species_id, species in {**proteins, **reactants}.items():
                rows.append(
                    [
                        measurement_id,
                        species_id,
                        str(species.init_conc),
                        species.unit
                    ]
                )

        # Add empty row for better readablity
        rows.append([" "] * 4)
        table.add_rows(rows)

        return f"\n{table.draw()}\n"

    def printReactionSchemes(self, by_name: bool = True):
        """Prints all reaction equations to inspect the content
        """

        output = []

        for reaction in self.reaction_dict.values():

            # Get the equation
            equation = reaction.get_reaction_scheme(
                by_name=by_name, enzmldoc=self
            )

            if self.in_ipynb():
                output.append(
                    {
                        "ID": reaction.id,
                        "Name": reaction.name,
                        "equation": equation.split("\n")[1].replace("Equation: ", ""),
                        "kinetic law": equation.split("\n")[2].replace("Model: v = ", "")
                    }
                )
            else:
                output.append(equation)

        if self.in_ipynb():
            return pd.DataFrame(output).set_index("ID")
        else:
            print("\n".join(output))

    @staticmethod
    def in_ipynb():
        """Checks whether in an ipynb or not"""
        try:
            cfg = get_ipython().config
            if get_ipython().__class__.__name__ == 'ZMQInteractiveShell':
                return True
            else:
                return False
        except NameError:
            return False

    def generateInitialValueTemplate(self, dir: str = ".") -> None:
        """Generates an initial value template as a YAML file, which can be used for modeling.

        Args:
            dir (str, optional): Dirpath to the output file. Defaults to ".".
        """

        init_values = {}

        for reaction in self.reaction_dict.values():

            if reaction.model is None:
                continue

            parameters = {
                param.name: None
                for param in reaction.model.parameters
            }

            init_values[reaction.id] = parameters

            # Finally, write the template to YAML
            out = os.path.join(dir, self.name.replace(
                " ", "_") + "_init_values.yaml"
            )

            with open(out, "w") as file_handle:
                yaml.dump(
                    init_values,
                    file_handle,
                    default_flow_style=False,
                    sort_keys=False
                )

    def applyModelInitialization(self, path: str, to_values: bool = False) -> None:
        """Adds initial values per reaction to the model from a YAML config file.

        This method loads a YAML that previously generated from the function 'generateInitialValueTemplate'
        and was filled with values. These are then used to populate the 'initial_value' fields of KineticParameter objects.

        Args:
            path (str): Path to the YAML file containing the initial values.
        """

        # Load the YAML file
        with open(path, "r") as file_handle:
            initial_values = yaml.safe_load(file_handle)

        # Apply all given initial values to the model
        for reaction_id, value_dict in initial_values.items():

            # Get the reaction
            reaction = self.getReaction(reaction_id)
            reaction.apply_initial_values(value_dict, to_values=to_values)

    # ! Add methods

    @validate_arguments
    def addCreator(self, creator: Creator, log: bool = True) -> str:
        """Adds a creator object to the EnzymeML document.

        Args:
            creator (Creator): Creator object to be added to the document.

        Returns:
            str: Unique internal identifier of the creator.
        """

        # Generate ID
        creator.id = self._generateID(prefix="a", dictionary=self.creator_dict)

        # Add to the document
        self.creator_dict[creator.id] = creator

        if log:
            # Log creator object
            log_object(logger, creator)
            logger.debug(
                f"Added {type(creator).__name__} ({creator.id}) '{creator.family_name}' to document '{self.name}'"
            )

        return creator.id

    @ validate_arguments
    def addVessel(self, vessel: Vessel, use_parser: bool = True) -> str:
        """Adds a Vessel object to the EnzymeML document.

        Args:
            vessel (Vessel): Vessel object to be added to the document.
            use_parser (bool, optional): Whether to user the unit parser or not. Defaults to True.

        Returns:
            str: Unique internal identifier of the reactant.
        """

        return self._addSpecies(
            species=vessel,
            prefix="v",
            dictionary=self.vessel_dict,
            use_parser=use_parser
        )

    @ validate_arguments
    def addReactant(self, reactant: Reactant, use_parser: bool = True) -> str:
        """Adds a Reactant object to the EnzymeML document.

        Args:
            reactant (Reactant): Reactant object to be added to the document.
            use_parser (bool, optional): Whether to user the unit parser or not. Defaults to True.

        Returns:
            str: Unique internal identifier of the reactant.
        """

        return self._addSpecies(
            species=reactant,
            prefix="s",
            dictionary=self.reactant_dict,
            use_parser=use_parser,
        )

    @ validate_arguments
    def addProtein(self, protein: Protein, use_parser: bool = True) -> str:
        """Adds a Protein object to the EnzymeML document.

        Args:
            protein (Protein): Protein object to be added to the document.
            use_parser (bool, optional): Whether to user the unit parser or not. Defaults to True.

        Returns:
            str: Unique internal identifier of the protein.
        """

        return self._addSpecies(
            species=protein,
            prefix="p",
            dictionary=self.protein_dict,
            use_parser=use_parser
        )

    @ validate_arguments
    def _add_complex(self, complex: Complex, use_parser: bool = True) -> str:
        """Adds a Complex object to the EnzymeML document.

        Args:
            complex (Complex): Complex object to be added to the document.
            use_parser (bool, optional): Whether to user the unit parser or not. Defaults to True.

        Returns:
            str: Unique internal identifier of the complex.
        """

        return self._addSpecies(
            species=complex,
            prefix="c",
            dictionary=self.complex_dict,
            use_parser=use_parser
        )

    @validate_arguments
    def addComplex(
        self,
        name: str,
        participants: list[str],
        vessel_id: str,
        init_conc: Optional[float] = None,
        unit: Optional[str] = None
    ):

        # First convert all participants given as name to IDs
        participants = [
            self.getAny(participant).id
            for participant in participants
        ]

        return self._add_complex(
            Complex(
                name=name,
                participants=participants,
                vessel_id=vessel_id,
                init_conc=init_conc,
                unit=unit
            )
        )

    def _addSpecies(
        self,
        species: Union[AbstractSpecies, Vessel],
        prefix: str,
        dictionary: dict,
        use_parser: bool = True,
        log: bool = True
    ) -> str:
        """Helper function to add any specific species to the EnzymeML document.

        Args:
            species (AbstractSpecies): Species that is about to be added to the EnzymeML document.
            prefix (str): Character that is used to generate a unique internal identifier.
            dictionary (dict): The dictionary where the species will be added to.
            use_parser (bool, optional): Whether to user the unit parser or not. Defaults to True.

        Returns:
            str: The internal identifier of the species.
        """

        # Generate ID
        species.id = self._generateID(
            prefix=prefix, dictionary=dictionary
        )
        species.meta_id = f"METAID_{species.id.upper()}"

        # Update unit to UnitDefID
        if species.unit and use_parser:
            unit_id = self._convertToUnitDef(species.unit)
            species._unit_id = unit_id
        elif species.unit and use_parser is False:
            species._unit_id = species.unit
            species.unit = self.getUnitString(species._unit_id)

        # Log creation of the object
        log_object(logger, species)

        # Add species to dictionary
        dictionary[species.id] = species

        # Log the addition
        if log:
            logger.debug(
                f"Added {type(species).__name__} ({species.id}) '{species.name}' to document '{self.name}'"
            )

        return species.id

    def addReaction(self, reaction: EnzymeReaction, use_parser: bool = True) -> str:
        """
        Adds EnzymeReaction object to EnzymeMLDocument object.
        Automatically assigns ID and converts units.

        Args:
            reaction (EnzymeReaction): Object describing reaction
            use_parser (bool, optional): If set True, will use
                                         internal unit parser.
                                         Defaults to True.

        Returns:
            string: Internal identifier for the reaction.
            Use it for other objects!
        """

        # Generate ID
        reaction.id = self._generateID("r", self.reaction_dict)
        reaction.meta_id = f"METAID_{reaction.id.upper()}"

        if use_parser and reaction.temperature:
            # Reset temperature for SBML compliance to Kelvin
            reaction.temperature = (
                reaction.temperature + 273.15
                if re.match(r"^K|kelvin", reaction.temperature_unit)
                else reaction.temperature
            )

            # Generate internal ID for the unit
            reaction._temperature_unit_id = self._convertToUnitDef(
                reaction.temperature_unit
            )
        elif reaction.temperature:
            # Set the temperature unit to the actual string
            reaction._temperature_unit_id = reaction.temperature_unit
            reaction.temperature_unit = self.getUnitString(
                reaction.temperature_unit
            )

        # Set model units and check for consistency
        if reaction.model:
            # ID consistency
            self._check_kinetic_model_ids(
                model=reaction.model
            )

            # Unit conversion
            self._convert_kinetic_model_units(
                reaction.model.parameters,
                enzmldoc=self
            )

        # Finally add the reaction to the document
        self.reaction_dict[reaction.id] = reaction

        # Log the object
        log_object(logger, reaction)
        logger.debug(
            f"Added {type(reaction).__name__} ({reaction.id}) '{reaction.name}' to document '{self.name}'"
        )

        return reaction.id

    def addReactions(self, reactions: list[EnzymeReaction]):
        """Adds multiple reactions to an EnzymeML document.

        Args:
            reactions (list[EnzymeReaction]): List of EnzymeReaction objects
        """

        return {
            reaction.name: self.addReaction(reaction)
            for reaction in reactions
        }

    def add_by_reaction_equation(self, equation: str, name: str):
        return EnzymeReaction.fromEquation(
            equation=equation,
            name=name,
            enzmldoc=self
        )

    def _check_kinetic_model_ids(self, model) -> None:
        """Checks if the given species IDs/names are consistent with the EnzymeML document. Also converts names into IDs, if given in the document.

        Args:
            equation (str): The rate law given in the KineticModel
        """

        # Get all the params of the model to distinguis params from names
        all_params = [param.name for param in model.parameters]

        for node in ast.walk(ast.parse(model.equation)):

            if isinstance(node, ast.Constant):
                # If the equation was generated  via the ModelFactory
                name = repr(node.value)
            elif isinstance(node, ast.Name):
                # If the equation has been done manually
                name = node.id

                if name in all_params:
                    # If its a parameter
                    continue
            else:
                continue

            if name not in self.getSpeciesIDs():

                try:
                    # Try to get by name and substitute in equation
                    species_id = self.getAny(
                        name.replace("'", ""),
                    ).id

                    model.equation = model.equation.replace(
                        name, species_id
                    )
                except StopIteration:
                    # If neither name or ID is found, raise Error
                    raise SpeciesNotFoundError(
                        enzymeml_part="Kinetic Model",
                        species_id=name
                    )

    @ staticmethod
    def _convert_kinetic_model_units(parameters: list[KineticParameter], enzmldoc) -> None:
        """Converts given unit strings to unit IDs and adds them to the model.

        Args:
            parameters (list[KineticParameter]): List of all kinetic parameters.
            enzmldoc ([type]): Used to convert unit strings to unit IDs.
        """

        for parameter in parameters:
            if parameter.unit:
                parameter._unit_id = enzmldoc._convertToUnitDef(parameter.unit)

    def addFile(
        self,
        filepath=None,
        file_handle=None,
        description="Undefined"
    ) -> str:
        """Adds any arbitrary file to the document. Please note, that if a filepath is given, any file_handle will be ignored.

        Args:
            filepath (str, optional): Path to the file that is added to the document. Defaults to None.
            file_handle (io.BufferedReader, optional): File handle that will be read to a bytes string. Defaults to None.

        Returns:
            str: Internal identifier for the file.
        """

        # Generate a unique identifier for the file
        file_id = self._generateID("f", self.file_dict)

        if filepath:
            # Open file handle
            file_handle = open(filepath, "rb")
        elif filepath is None and file_handle is None:
            raise ValueError(
                "Please specify either a file path or a file handle"
            )

        # Finally, add the file and close the handler
        self.file_dict[file_id] = {
            "name": os.path.basename(file_handle.name),
            "handler": file_handle,
            "description": description
        }

        return file_id

    @ validate_arguments
    def addMeasurement(self, measurement: Measurement) -> str:
        """Adds a measurement to an EnzymeMLDocument and validates consistency with already defined elements of the document.

        Args:
            measurement (Measurement): Collection of data and initial concentrations per reaction

        Returns:
            measurement_id (String): Assigned measurement identifier.
        """

        # Check consistency
        self._checkMeasurementConsistency(measurement)

        # Convert all measurement units to UnitDefs
        self._convertMeasurementUnits(measurement)

        # Generate the ID and add it to the dictionary
        measurement.id = self._generateID(
            prefix="m", dictionary=self.measurement_dict
        )

        # Update measurement ID to all replicates
        protein_data = measurement.species_dict["proteins"]
        reactant_data = measurement.species_dict["reactants"]

        self._updateReplicateMeasurementIDs(protein_data, measurement.id)
        self._updateReplicateMeasurementIDs(reactant_data, measurement.id)

        # Add it to the EnzymeMLDocument
        self.measurement_dict[measurement.id] = measurement

        # Log the object
        log_object(logger, measurement)
        logger.debug(
            f"Added {type(measurement).__name__} ({measurement.id}) '{measurement.name}' to document '{self.name}'"
        )

        return measurement.id

    def _convertMeasurementUnits(self, measurement: Measurement) -> None:
        """Converts string SI units to UnitDef objects and IDs

        Args:
            measurement (Measurement): Object defining a measurement
        """

        # Update global time of the measurement
        if measurement.global_time:
            measurement._global_time_unit_id = self._convertToUnitDef(
                measurement.global_time_unit
            )

        # Update temperature unit of the measurement
        if measurement.temperature_unit:
            measurement._temperature_unit_id = self._convertToUnitDef(
                measurement.temperature_unit
            )

        def update_dict_units(measurement_data_dict: dict[str, MeasurementData]) -> None:
            """Helper function to update units"""
            for measurement_data in measurement_data_dict.values():
                measurement_data._unit_id = self._convertToUnitDef(
                    measurement_data.unit
                )

                global_time = self._convertReplicateUnits(
                    measurement_data
                )

                if global_time:
                    measurement.global_time = global_time

        # Perform update
        update_dict_units(measurement.species_dict["proteins"])
        update_dict_units(measurement.species_dict["reactants"])

    def _convertReplicateUnits(self, measurement_data: MeasurementData) -> Optional[list[float]]:
        """Converts replicate unit strings to unit definitions.

        Args:
            measurement_data (MeasurementData): Object holding measurement data for a species
        """

        # TODO verify globally global time
        global_time = None

        for replicate in measurement_data.replicates:

            # Convert unit
            time_unit_id = self._convertToUnitDef(replicate.time_unit)
            data_unit_id = self._convertToUnitDef(replicate.data_unit)

            # Assign unit IDs
            replicate._data_unit_id = data_unit_id
            replicate._time_unit_id = time_unit_id

            global_time = replicate.time

        return global_time

    def _updateReplicateMeasurementIDs(self, measurement_data_dict: dict[str, MeasurementData], measurement_id: str):
        """Updates the measurement IDs of replicates."""
        for measurement_data in measurement_data_dict.values():
            replicates = measurement_data.replicates
            for replicate in replicates:
                replicate.measurement_id = measurement_id

    def _checkMeasurementConsistency(self, measurement: Measurement) -> None:
        """Checks if the used species in the measurement are consistent with the EnzymeML document.

        Args:
            measurement (MeasurementData): Objech holding measurement data for a species.
        """

        map(self._checkSpecies, measurement.species_dict["reactants"])
        map(self._checkSpecies, measurement.species_dict["proteins"])

    def _checkSpecies(self, species_id):
        """Checks if a species is defined in the EnzymeML document.

        Args:
            species_id (str): Unique identifier of the species.

        Raises:
            SpeciesNotFoundError: Raised when a species is not defined in the EnzymeML document.
        """

        all_species = {
            **self.reactant_dict,
            **self.protein_dict,
            **self.complex_dict
        }

        if species_id not in all_species.keys():

            # Retrieve species for ontology
            species = self._getSpecies(
                id=species_id,
                dictionary=all_species,
                element_type="Proteins/Reactants/Complexes"
            )

            # Use the EnzymeMLPart Enum to derive the correct place
            sbo_term = SBOTerm(species.__dict__["ontology"]).name
            enzymeml_part = EnzymeMLPart.partFromSBOTerm(sbo_term)

            # Raise an error if the species is nowhere present
            raise SpeciesNotFoundError(
                species_id=species_id,
                enzymeml_part=enzymeml_part
            )

    def _convertToUnitDef(self, unit: Optional[str]) -> str:
        """Reads an SI unit string and converts it into a EnzymeML compatible UnitDef

        Args:
            unit (str): String representing the SI unit.

        Returns:
            str: Unique identifier of the UnitDef.
        """

        if unit is None:
            raise TypeError("No unit given.")
        elif unit in self.unit_dict.keys():
            return unit

        return UnitCreator().getUnit(unit, self)

    # ! Getter methods
    def getSpeciesIDs(self) -> list[str]:
        return list({
            **self.protein_dict,
            **self.reactant_dict,
            **self.complex_dict
        }.keys())

    def getUnitString(self, unit_id: Optional[str]) -> str:
        """Return the unit name corresponding to the given unit ID.

        Args:
            unit_id (str): Unique internal ID of the unit.

        Raises:
            SpeciesNotFoundError: Raised when the requested unit is not found.

        Returns:
            str: String representation of the unit.
        """

        if unit_id is None:
            raise TypeError("No unit given.")

        try:
            return self.unit_dict[unit_id].name
        except KeyError:
            raise SpeciesNotFoundError(
                species_id=unit_id, enzymeml_part="Units"
            )

    def getUnitDef(self, id: str) -> UnitDef:
        """Returns the unit associated with the given ID.

        Args:
            id (str): Unique internal ID of the unit.

        Raises:
            SpeciesNotFoundError: Raised when the requested unit is not found.

        Returns:
            UnitDef: The corresponding unit object.
        """

        return self._getSpecies(
            id=id,
            dictionary=self.unit_dict,
            element_type="Units",
        )

    def getVessel(self, id: str) -> Vessel:
        """Returns the vessel associated with the given ID.

        Args:
            id (str): Unique internal ID of the vessel.

        Raises:
            SpeciesNotFoundError: Raised when the requested vessel is not found.

        Returns:
            Vessel: The corresponding unit object.
        """

        return self._getSpecies(
            id=id,
            dictionary=self.vessel_dict,
            element_type="Vessels",
        )

    def getReaction(self, id: str) -> EnzymeReaction:
        """Returns the reaction associated with the given ID.

        Args:
            id (str): Unique internal ID of the reaction.

        Raises:
            SpeciesNotFoundError: Raised when the requested reaction is not found.

        Returns:
            EnzymeReaction: The corresponding reaction object.
        """

        return self._getSpecies(
            id=id,
            dictionary=self.reaction_dict,
            element_type="EnzymeReaction",
        )

    def getMeasurement(self, id: str) -> Measurement:
        """Returns the measurement associated with the given ID.

        Args:
            id (str): Unique internal ID of the measurement.

        Raises:
            SpeciesNotFoundError: Raised when the requested measurement is not found.

        Returns:
            Measurement: The corresponding measurement object.
        """

        return self._getSpecies(
            id=id,
            dictionary=self.measurement_dict,
            element_type="Measurement",
        )

    def getReactant(self, id: str) -> Reactant:
        """Returns the reactant associated with the given ID.

        Args:
            id (str): Unique internal ID of the reactant.

        Raises:
            SpeciesNotFoundError: Raised when the requested reactant is not found.

        Returns:
            Reactant: The corresponding reactant object.
        """

        return self._getSpecies(
            id=id,
            dictionary=self.reactant_dict,
            element_type="Reactant",
        )

    def getProtein(self, id: str) -> Protein:
        """Returns the protein associated with the given ID.

        Args:
            id (str): Unique internal ID of the protein.

        Raises:
            SpeciesNotFoundError: Raised when the requested protein is not found.

        Returns:
            Protein: The corresponding protein object.
        """

        return self._getSpecies(
            id=id,
            dictionary=self.protein_dict,
            element_type="Protein",
        )

    def getFile(self, id: str, by_id: bool = True) -> dict:
        """Returns the file associated with the given ID.

        Args:
            id (str): Unique internal ID of the file.

        Raises:
            SpeciesNotFoundError: Raised when the requested file is not found.

        Returns:
            dict[str, dict]: The corresponding file object.
        """

        if by_id:
            return self.file_dict[id]
        else:
            return next(filter(
                lambda file: file["name"] == id,
                self.file_dict.values()
            ))

    def getAny(self, id: str) -> AbstractSpecies:
        """Returns anything associated with the given ID.

        Args:
            id (str): Unique internal ID of the object.

        Raises:
            SpeciesNotFoundError: Raised when the requested object is not found.

        Returns:
            dict[str, dict]: The corresponding file object.
        """

        all_dicts = {
            **self.unit_dict,
            **self.vessel_dict,
            **self.reactant_dict,
            **self.protein_dict,
            **self.complex_dict,
            **self.reaction_dict
        }

        return self._getSpecies(
            id=id,
            dictionary=all_dicts,
            element_type="Document",
        )

    def _getSpecies(
        self,
        id: str,
        dictionary: dict,
        element_type: str,
    ):
        """Helper function to retrieve any kind of species from the EnzymeML document.

        Args:
            id (str): Unique internal ID.
            dictionary (dict): Dictionary that stores all objects.
            element_type (str): Type of object that is in the dictionary.

        Raises:
            SpeciesNotFoundError: Raised when the requested species is not found.

        Returns:
            Union[ AbstractSpecies, EnzymeReaction, Measurement ]: The requested object
        """

        for attr in ["id", "name"]:
            species = self._search_object(
                value=id, attr=attr, dictionary=dictionary
            )

            if species:
                return species

        raise SpeciesNotFoundError(
            species_id=id, enzymeml_part=element_type
        )

    def _search_object(self, value, attr: str, dictionary: dict):
        """Filters a given dictionary for an attributes and returns it if found.

        Args:
            value ([type]): Term that is searched for.
            attr (str): Corresponding attribute to look for.
            dictionary (dict): Dictionary that si searched.

        Returns:
            AbstractSpecies: Species from the EnzymeML document.
        """

        try:
            # Filter the dict for the desired species
            return next(filter(
                lambda obj: obj.__dict__[attr] == value,
                dictionary.values()
            ))
        except StopIteration:
            return None

    def getReactantList(self) -> list[Reactant]:
        """Returns a list of all reactants in the EnzymeML document."

        Returns:
            list[Reactant]: List of all reactants in the EnzymeML document.
        """
        return self._getSpeciesList(self.reactant_dict)

    def getProteinList(self) -> list[Protein]:
        """Returns a list of all proteins in the EnzymeML document."

        Returns:
            list[Protein]: List of all proteins in the EnzymeML document.
        """
        return self._getSpeciesList(self.protein_dict)

    def getReactionList(self) -> list[EnzymeReaction]:
        """Returns a list of all reactions in the EnzymeML document."

        Returns:
            list[EnzymeReaction]: List of all reactions in the EnzymeML document.
        """
        return self._getSpeciesList(self.reaction_dict)

    def getFilesList(self):
        """Returns a list of all files in the EnzymeML document."

        Returns:
            list[dict]: List of all files in the EnzymeML document.
        """
        return self._getSpeciesList(self.file_dict)

    @ staticmethod
    def _getSpeciesList(dictionary: dict) -> list:
        """Helper function to retrieve lists of dicitonary objects

        Args:
            dictionary (dict): Dictionary of corresponding elements

        Returns:
            list: Returns all values in the dictionary
        """
        return list(dictionary.values())

    @ deprecated_getter("doi")
    def getDoi(self) -> Optional[str]:
        return self.doi

    @ deprecated_getter("pubmedid")
    def getPubmedID(self) -> Optional[str]:
        return self.pubmedid

    @ deprecated_getter("url")
    def getUrl(self) -> Optional[str]:
        return self.url

    @ deprecated_getter("created")
    def get_created(self):
        return self.created

    @ deprecated_getter("modified")
    def getModified(self):
        return self.modified

    @ deprecated_getter("creators")
    def getCreator(self):
        return self.creator_dict

    @ deprecated_getter("name")
    def getName(self):
        return self.name

    @ deprecated_getter("level")
    def getLevel(self):
        return self.level

    @ deprecated_getter("version")
    def getVersion(self):
        return self.version

    @ deprecated_getter("protein_dict")
    def getProteinDict(self):
        return self.protein_dict

    @ deprecated_getter("reactant_dict")
    def getReactantDict(self):
        return self.reactant_dict

    @ deprecated_getter("reaction_dict")
    def getReactionDict(self):
        return self.reaction_dict

    @ deprecated_getter("measurement_dict")
    def getMeasurementDict(self):
        return self.measurement_dict

    @ deprecated_getter("unit_dict")
    def getUnitDict(self):
        return self.unit_dict

    @ deprecated_getter("file_dict")
    def getFileDict(self):
        return self.file_dict
