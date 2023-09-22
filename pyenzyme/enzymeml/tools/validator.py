# File: validator.py
# Project: core
# Author: Jan Range
# License: BSD-2 clause
# Copyright (c) 2022 Institute of Biochemistry and Technical Biochemistry Stuttgart

import importlib
import logging
import re
import yaml
import os
import pandas as pd

from itertools import cycle
from typing import Optional, Dict, Tuple, List

from pyenzyme.enzymeml.core.unitdef import UnitDef

# Set up a logger for validation
logger = logging.getLogger("validator")
logger.setLevel(logging.WARNING)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.WARNING)

# create formatter
formatter = logging.Formatter("ValidationWarning: %(message)s")

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)


class EnzymeMLValidator:
    def __init__(self, scheme: Dict):
        """Initialize a Validator instance that is capapble to find non-compliances.


        Args:
            scheme (dict): EnzymeML object model for every attribute including options to check upon.
        """

        self.scheme = scheme

    # ! Validation of EnzymeMLDocuments
    def validate(self, enzmldoc) -> Tuple[Dict, bool]:
        """Validate an EnzymeMLDocument based on a given scheme, let it be YAML or XLSX.

        Args:
            enzmldoc (EnzymeMLDocument): EnzymeMLDocument that will be validated and reported on.
            return_report (bool): Whether or not an error should raised or only then report should be returned when validation fails. Please note, thsi behaviour should remain
        """

        return self._validate_objects(obj=enzmldoc.dict(), valid=self.scheme)

    @classmethod
    def _validate_objects(cls, obj, valid: Dict) -> Tuple[Dict, bool]:
        """Validates sub-objects of an EnzymeMLDocument"""

        # Initialize report and control list
        report, valid_check = {}, []

        for attrib, value in obj.items():
            if not valid.get(attrib):
                # Skip attributes not supported
                continue

            if attrib == "model":
                # Model can be None, thus it needs special treatment
                obj_report, check = cls._validate_objects(value, valid[attrib])

            elif isinstance(value, dict):
                if attrib == "species_dict":
                    # Measurements species_dict needs to be flattened
                    value = {**value["proteins"], **value["reactants"]}

                # Perform validation on dict struct
                cls._validate_iterator(
                    value.items(), attrib, valid, valid_check, report
                )

            elif isinstance(value, list):
                if not all(isinstance(x, (float, int, str)) for x in value):
                    # If its an actual list of objects
                    cls._validate_iterator(
                        enumerate(value), attrib, valid, valid_check, report
                    )

            else:
                # Any primitive file gets validated here
                obj_report, check = cls._validate_field(value, valid[attrib], attrib)

                if obj_report:
                    # Only add if non-empty
                    report[attrib] = obj_report

                valid_check += [check]

        return report, all(valid_check)

    @classmethod
    def _validate_iterator(cls, iterator, attrib, valid, check, global_report):
        """Validates an arbitrary data structure if given as an iterator"""

        # Initialize local report
        local_report = {}

        for id, obj in iterator:
            report, is_valid = cls._validate_objects(obj, valid[attrib])

            if report:
                # Only add if report is non-empty
                local_report[id] = report
                check += [is_valid]

        # Only add to global report if there are errors
        if local_report:
            global_report[attrib] = local_report

    @staticmethod
    def _validate_field(value, valid, attrib):
        """Validates an attribute based on options given from a YAML file"""

        if "id" in attrib:
            return {}, True

        report, check = {}, True
        enum = valid["enum"]
        val_min = valid["range"]["min"]
        val_max = valid["range"]["max"]

        if all(val is None for val in enum):
            enum = None

        # Check mandatory
        if value is None and valid["mandatory"] is True:
            check = False
            report.update({"mandatory_error": "Mandatory attribute is not given."})

        # Check enum
        if enum and value not in enum:
            check = False
            report.update(
                {
                    "enum_error": f"Value of '{value}' does not comply with vocabulary {enum}"
                }
            )

        # Check value range
        if val_max and val_min:
            if isinstance(value, (int, float)):
                if not val_min <= value <= val_max:
                    check = False
                    report.update(
                        {
                            "range_error": f"Value of '{value}' is out of range for [{val_min}, {val_max}]"
                        }
                    )

            else:
                check = False
                report.update(
                    {
                        "range_error": f"Value '{value}' of type '{type(value)}' is not numeric."
                    }
                )

        return report, check

    # ! Template exports
    @classmethod
    def generateValidationSpreadsheet(cls, path: str = "."):
        """Generates an EnzymeML validation spreadsheet based on the current implementation.

        The Validation spreadsheet can be used on database-side to generate an EnzymeML validation
        YAML file that can be used by PyEnzyme to validate if a given document fits the minimal
        requirements given in said database.
        """

        # Prevent circular imports (Its dirty, I know, but it works)
        from pyenzyme.enzymeml.core.enzymemldocument import EnzymeMLDocument

        # Get all specs
        validator = cls(scheme={})
        _, data = validator._get_cls_annotations(EnzymeMLDocument, level="document")

        # Generate the document
        validator._generate_spreadsheet(data, path)

    @classmethod
    def generateValidationYAML(cls, path: Optional[str] = None) -> str:
        """Generates an EnzymeML validation YAML file based on the current implementation.

        The Validation YAML can be used by PyEnzyme to validate if a given document fits the minimal
        requirements given in said database.
        """

        # Prevent circular imports (Its dirty, I know, but it works)
        from pyenzyme.enzymeml.core.enzymemldocument import EnzymeMLDocument

        # Get collection data
        cls = cls(scheme={})
        collection, _ = cls._get_cls_annotations(EnzymeMLDocument, level="document")

        if path:
            path = os.path.join(path, "EnzymeML_Validation_Template.yaml")
            with open(path, "w") as f:
                f.write(cls._dump_validation_template_yaml(collection))

        return cls._dump_validation_template_yaml(collection)

    def _get_cls_annotations(self, cls, level: str) -> Tuple[Dict, List]:
        """Parses class definitions to recursively get sub-modules"""

        data = []
        cls_collection = {}
        exclude = [
            "unit_dict",
            "file_dict",
            "log",
            "level",
            "version",
            "meta_id",
            "id",
            "boundary",
            "uri",
            "creator_id",
        ]

        # Sort annotations to primitive -> sub-structure
        def sort_func(annot):
            """Sort recursion for clean parsing"""
            data_type = repr(annot[1])
            if "pyenzyme" in data_type:
                return True
            else:
                return False

        annotations = sorted(cls.__annotations__.items(), key=sort_func)

        for name, value in annotations:

            if "pyenzyme.enzymeml" in repr(value) and "ontology" not in repr(value):

                annot = repr(value)
                regex = r"(pyenzyme.enzymeml.[a-zA-Z]*.[a-zA-Z]*).([a-zA-Z]*)"
                regex = re.compile(regex)
                module, cls_name = regex.findall(annot)[0]

                sub_class = getattr(importlib.import_module(module), cls_name)

                if name not in exclude:
                    cls_collection[name], sub_data = self._get_cls_annotations(
                        sub_class, level=name
                    )
                    data += sub_data

                continue

            if not name.startswith("_") and name not in exclude:

                options = {
                    "mandatory": True,
                    "description": cls.__fields__[name].field_info.description,
                }

                data_fields = {
                    "Object": cls.__name__,
                    "Field": name,
                    "Mandatory": "True",
                    "Value Range": "Enter Min to Max value",
                    "Controlled Vocabulary": "Enter a set of allowed names/values",
                    "Description": cls.__fields__[name].field_info.description,
                    "Internal Level (not relevant)": level,
                }

                options["range"] = {"min": None, "max": None}
                data_fields["Controlled Vocabulary"] = "---"
                options["enum"] = [None]
                data_fields["Value Range"] = "---"

                cls_collection[name] = options
                data.append(data_fields)

        return cls_collection, data

    @staticmethod
    def _dump_validation_template_yaml(collection: Dict) -> str:
        class MyDumper(yaml.Dumper):
            def increase_indent(self, flow=False, indentless=False):
                return super(MyDumper, self).increase_indent(flow, False)

        # Generate yaml_string
        return yaml.dump(
            collection, Dumper=MyDumper, default_flow_style=False, sort_keys=False
        )

    @staticmethod
    def _generate_spreadsheet(data, path):
        """Generates an EnzymeML validation spreadsheet based on the current implementation.

        The Validation spreadsheet can be used on database-side to generate an EnzymeML validation
        YAML file that can be used by PyEnzyme to validate if a given document fits the minimal
        requirements given in said database.

        Args:
            data (dict): Schema that has been extracted from the EnzymeMLDocument class.

        """

        # Initialize writer and setup a DataFrame to write to
        writer = pd.ExcelWriter(os.path.join(path, "EnzymeML_Validation_Template.xlsx"))
        df = pd.DataFrame(data)
        df.to_excel(writer, sheet_name="validation", index=False, na_rep="NaN")

        # Create color cycle that will be used to mark different objects
        colors = cycle(
            [
                "#FFEBEE",
                "#F3E5F5",
                "#E8EAF6",
                "#E3F2FD",
                "#E0F7FA",
                "#E8F5E9",
                "#F9FBE7",
                "#FFFDE7",
                "#FBE9E7",
            ]
        )

        # Process colummns
        # Auto-adjust columns' width
        for column in df:
            column_width = max([len(str(value)) for value in df[column]])

            if column_width <= 20:
                # Keep columns at a min width
                column_width = 20

            col_idx = df.columns.get_loc(column)
            writer.sheets["validation"].set_column(col_idx, col_idx, column_width)

        # Process rows
        # Set height of first row
        workbook = writer.book
        style = workbook.add_format()
        style.set_align("left")
        writer.sheets["validation"].set_row(0, 25, style)

        obj = None
        for row_idx, row in df.iterrows():

            workbook = writer.book
            style = workbook.add_format()
            style.set_align("center_across")
            style.set_text_h_align("left")

            if obj != row["Object"]:
                # Object changes
                current_color = next(colors)
                obj = row["Object"]

                # Set borders to top == bold
                style.set_left(1)
                style.set_right(1)
                style.set_left_color("#9E9E9E")
                style.set_right_color("#9E9E9E")
                style.set_top(1)

            else:
                # Same object, keep normal border pattern
                style.set_border(1)
                style.set_border_color("#9E9E9E")

            # Set the background color of the row
            style.bg_color = current_color

            # Write to row
            writer.sheets["validation"].set_row(row_idx + 1, 25, style)

        writer.close()

    # ! Template conversion
    @classmethod
    def convertSheetToYAML(cls, path: str, filename: Optional[str] = None) -> str:
        """Converts a given EnzymeML Validation spreadsheet to a valid EnzymeML validation YAML file.

        The generated file can be hosted in a database where it is publicaly available to
        validate EnzymeML documents based on the minimal requirements defined in the YAML file.
        It can also serve as a local file to validate to your own requirements.

        If a filename has been given, the YAML file will be written to the same directory
        as the spreadsheet template. Otherwise

        Args:

            path (str): Path to the EnzymeML Validation spreadsheet
            filename (Optional[str]): Name of the generated YAML file, if specified. Defaults to None.

        Returns:

            str: Generated YAML file string.

        """

        # Prevent circular imports (Its dirty, I know, but it works)
        from pyenzyme.enzymeml.core.enzymemldocument import EnzymeMLDocument

        # Read template and get class structure collection
        cls = cls(scheme={})
        template = pd.read_excel(path).to_dict(orient="records")
        empty_collection, _ = cls._get_cls_annotations(
            EnzymeMLDocument, level="document"
        )

        for entry in template:

            # Get everything from the entry
            level = entry["Internal Level (not relevant)"]
            field = entry["Field"]
            mandatory = entry["Mandatory"]
            val_range = entry["Value Range"]
            enum = entry["Controlled Vocabulary"]

            # Process given values
            if enum in ["Enter a set of allowed names/values", "---"]:
                enum = [None]
            else:
                enum = [val.strip() for val in enum.split(",")]

            if val_range in ["Enter Min to Max value", "---"]:
                min, max = None, None
            else:
                values = [float(val.strip()) for val in val_range.split("-")]
                min, max = values[0], values[1]

            # Retrieve fitting object from collection
            if level == "document":
                # Root level
                collection_obj = empty_collection
            else:
                # Sub-root object
                collection_obj = cls._traverse_data(empty_collection, level)

            # Apply changes to the empty collection
            field_options = collection_obj[field]
            field_options.update(
                {
                    "mandatory": mandatory,
                    "enum": enum,
                    "range": {"min": min, "max": max},
                }
            )

        # Get the yaml string
        yaml_string = cls._dump_validation_template_yaml(empty_collection)

        if filename:
            path = os.path.dirname(os.path.abspath(path))
            yaml_path = os.path.join(path, f"{filename}.yaml")

            with open(yaml_path, "w") as f:
                f.write(yaml_string)

        return yaml_string

    @classmethod
    def _traverse_data(cls, data, search_term: str) -> Optional[Dict]:
        """Traverses a dictionary and returns the object reference"""

        # Adapt to file types
        if isinstance(data, dict):
            fields = data.items()
        elif isinstance(data, list):
            fields = enumerate(data)
        else:
            raise TypeError(f"Invalid data type {type(data)}")

        result = None

        for key, item in fields:
            if search_term == key:
                return item
            elif isinstance(item, (dict, list)):
                result = cls._traverse_data(item, search_term)

                if result:
                    return result

        return None

    # ! Unit checker
    @classmethod
    def check_unit_consistency(cls, enzmldoc, strict: bool = False):
        """Validates unit consistency in an EnzymeMLDocument.

        This method will check whether all (initial) concentration units of a species
        are consistent throughout the document. Default mode only requires measurements and
        replicates to comply to the species unit.

        This can also be set to 'strict', where any species, measurement,
        replicate and parameter has to comply in a global fashion.
        To summarise, strict mode checks on:

            - Consistent usage of time
            - Consistent concentration units for ALL concentrations
            - Consistent volumetric unit including vessels

        Strict mode is of greates importance for kinetic modeling, differing scales
        can lead to wrong results. However, the code will still run and only warnings
        will be given.

        Args:
            strict (bool, optional): _description_. Defaults to False.

        Returns:
            Dict: Report on which units are inconsistent
            Bool: Whether the document is consistent in units
        """

        # Initialize validator to use
        cls = cls(scheme={})

        # Now create a data structure of units per species for
        # Measurements and Replicates
        used_units = {}
        used_time_units = {}
        used_volume_units = {}
        report, is_consistent = {}, True

        # Check vessel unit
        cls._check_vessels(enzmldoc, used_volume_units)

        # Perform consistency check on parameters
        cls._check_parameters(enzmldoc, used_time_units, used_volume_units)

        # Perform consistency check on species/replicates/measurements
        cls._check_species(
            enzmldoc, report, used_time_units, used_units, used_volume_units
        )

        if strict:

            if len(set(used_units.values())) != 1:
                logger.warning(
                    f"Inconsistent usage of concentration units. All units should be the same, but found {set(used_units.values())}"
                )

                # Append to report
                report["conc_units"] = cls._reformat_strict_report(used_units)

            if len(set(used_time_units.values())) != 1:
                logger.warning(
                    f"Inconsistent usage of time units. All units should be the same, but found {set(used_time_units.values())}"
                )

                # Append to report
                report["time_units"] = cls._reformat_strict_report(used_time_units)

            if len(set(used_volume_units.values())) != 1:
                logger.warning(
                    f"Inconsistent usage of volume units. All units should be the same, but found {set(used_volume_units.values())}. In order to guarantee modelling platforms based on SBML to work properly, make sure that vessel volume unit is consistent with the one used in concentration. \n\nBest done by editing vessels using 'enzmldoc.getVessel(ID)' and an appropriate 'unit' assigned along with a rescaling."
                )

                # Append to report
                report["volume_units"] = cls._reformat_strict_report(used_volume_units)

        if report:
            is_consistent = False

        return is_consistent, report

    def _check_vessels(self, enzmldoc, used_volume_units: Dict[str, str]):
        """Checks volumetric unit consitency of Vessels"""

        for vessel in enzmldoc.vessel_dict.values():
            vessel_unit = vessel.unitdef()
            volume_part = self._get_baseunit_part(vessel_unit, kind="litre")

            if volume_part:
                used_volume_units[vessel.id] = volume_part[0].get_name()

    def _check_parameters(
        self,
        enzmldoc,
        used_time_units: Dict[str, str],
        used_volume_units: Dict[str, str],
    ) -> None:
        """Checks time unit consistency of Parameters"""

        # Get all the time units used in parameters
        # Export local parameters
        params = [
            param
            for reaction in enzmldoc.reaction_dict.values()
            for param in reaction.model.parameters
            if reaction.model and not param.is_global
        ]

        # Global parameters
        params += [param for param in enzmldoc.global_parameters.values()]

        for param in params:
            if param.unit:

                # Get the time unit, if given
                time_part = self._get_baseunit_part(param.unitdef(), "second")

                if time_part:
                    # When there is a time unit, store it
                    used_time_units[param.name] = time_part[0].get_name()

                # Get the volume unit, if given
                volume_part = self._get_baseunit_part(param.unitdef(), "litre")

                if volume_part:
                    # When there is a time unit, store it
                    used_volume_units[param.name] = volume_part[0].get_name()

    def _check_species(
        self,
        enzmldoc,
        report: Dict,
        used_time_units: Dict[str, str],
        used_units: Dict[str, str],
        used_volume_units: Dict[str, str],
    ):
        """Checks consistency for species to measurements"""

        all_species = {
            **enzmldoc.protein_dict,
            **enzmldoc.reactant_dict,
            **enzmldoc.complex_dict,
        }

        for id, species in all_species.items():

            # Get the unit expected from the species
            unit = species.unitdef()

            # If there is no unit at the species, take the
            # first from a measurement
            if unit:
                unit_name = unit._get_unit_name()
                used_units[id] = unit_name
            else:
                logger.warning(
                    f"{species.__class__.__name__} {id} has no unit specified. Using measurement unit as reference now. Use 'strict' to force units at species.",
                )
                used_units[id] = "No Unit"
                unit_name = None

            # Initialize a dict to report on where units are inconsistent
            log_dict = {"measurements": {}, "replicates": {}}

            for measurement in enzmldoc.measurement_dict.values():
                meas_species = measurement._getAllSpecies()
                meas_data = meas_species.get(id)

                if meas_data:

                    # Get measurement unit
                    meas_data = meas_species.get(id)
                    meas_unit = meas_data.unitdef()
                    meas_unit_name = meas_unit._get_unit_name()
                    meas_vol_unit = self._get_baseunit_part(meas_unit, "litre")

                    if unit is None:
                        # Use meas unit as the expected one
                        unit = meas_unit
                        unit_name = meas_unit._get_unit_name()

                    # Add to list of already used units
                    location = f"{measurement.id}/{meas_data.get_id()}"
                    used_units[location] = meas_unit_name
                    used_time_units[location] = measurement.global_time_unit

                    # If there is a volumetric unit, add it
                    if meas_vol_unit:
                        used_volume_units[location] = meas_vol_unit[0].get_name()

                    if unit_name != meas_unit_name:
                        # Report if there are inconsistencies
                        log_dict["measurements"][measurement.id] = {
                            "expected": unit._get_unit_name(),
                            "given": meas_unit_name,
                        }

                    # Check replicates
                    for replicate in meas_data.replicates:

                        # Get replicate units
                        repl_unit = replicate.data_unitdef()
                        repl_unit_name = repl_unit._get_unit_name()
                        repl_vol_unit = self._get_baseunit_part(repl_unit, "litre")

                        # Add to list of already used units
                        location = (
                            f"{measurement.id}/{meas_data.get_id()}/{replicate.id}"
                        )
                        used_units[location] = meas_unit_name
                        used_time_units[location] = measurement.global_time_unit

                        # If there is a volumetric unit, add it
                        if meas_vol_unit:
                            used_volume_units[location] = repl_vol_unit[0].get_name()

                        if unit_name != repl_unit_name:
                            # Report if there are inconsistencies
                            log_dict["replicates"][measurement.id] = {
                                "expected": unit._get_unit_name(),
                                "given": repl_unit_name,
                            }

            # Add to the overall report
            if log_dict["measurements"] or log_dict["replicates"]:
                report[id] = {key: report for key, report in log_dict.items() if report}

    @staticmethod
    def _reformat_strict_report(report: Dict[str, str]):
        """Reformats a report for improved redability"""

        # Get all values that occur
        values = list(set(report.values()))
        nu_report = {}

        # Iterate over all those values and collect those entries that
        # posses the said object
        for value in values:
            nu_report[value] = [loc for loc, unit in report.items() if unit == value]

        return nu_report

    @staticmethod
    def _get_baseunit_part(unitdef: UnitDef, kind: str):
        """Gets a specific part of a unitdef"""

        return list(
            filter(
                lambda baseunit: baseunit.kind == kind,
                unitdef.units,
            )
        )
