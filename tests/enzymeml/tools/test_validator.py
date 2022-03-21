import os
import yaml
import pandas as pd

from pyenzyme.enzymeml.tools.validator import EnzymeMLValidator
from pyenzyme.enzymeml.core.enzymemldocument import EnzymeMLDocument


class TestValidation:
    def test_positive_validation(self, enzmldoc, always_pass):
        """Tests positive validation with a non-restrictive validation YAML"""

        # Set up validator
        validator = EnzymeMLValidator(scheme=always_pass)

        # Perform validation
        report, check = validator.validate(enzmldoc)

        assert check is True
        assert not report, "Report is not empty"

    def test_negative_validation(self, enzmldoc, should_fail):
        """Tests negative validation with a restrictive validation YAML"""

        # Set up validator
        validator = EnzymeMLValidator(scheme=should_fail)

        # Perform validation and assertit failed
        report, check = validator.validate(enzmldoc)

        assert check is False
        assert report, "Report is empty"

    def test_creation_to_conversion(self):
        """Tests the complete path from EnzymeMLDocument class over Spreadhseet back to dict structure"""

        # Generate sheet
        sheet_path = "./tests/fixtures/"
        sheet_loc = os.path.join(sheet_path, "EnzymeML_Validation_Template.xlsx")
        EnzymeMLValidator.generateValidationSpreadsheet(path=sheet_path)

        assert pd.read_excel(sheet_loc).to_dict()

        # Manually create collection and compare it
        # to the one that will be drawn from the sheet
        collection = EnzymeMLValidator(scheme={})._get_cls_annotations(
            EnzymeMLDocument, level="document"
        )[0]
        expected = yaml.safe_load(
            EnzymeMLValidator._dump_validation_template_yaml(collection)
        )
        converted = yaml.safe_load(EnzymeMLValidator.convertSheetToYAML(sheet_loc))

        assert converted == expected, "Conversion from spreadsheet is inconsistent"

        # Remove everything
        os.remove(sheet_loc)

    def test_check_unit_consistency_positive(self, enzmldoc):
        """Checks whether unit consistency checkup behaves correctly - Positive case"""

        # Set vessel to "l" to get a positive result
        enzmldoc.vessel_dict["v0"].unit = "l"

        # Test default mode - Positive outcome
        is_consistent, report = EnzymeMLValidator.check_unit_consistency(enzmldoc)

        assert is_consistent
        assert not report

        # Test strict mode - Positive outcome
        is_consistent, report = EnzymeMLValidator.check_unit_consistency(
            enzmldoc, strict=True
        )

        assert is_consistent
        assert not report

    def test_check_unit_consistency_strict_mode_conc(self, enzmldoc):
        """Test strict mode and change units for all objects of a species (should fail, default works)"""

        # Manipulate document to force inconsistency
        # On species level
        enzmldoc.reactant_dict["s0"].unit = "fmole / l"

        # On measurement data level
        meas_data = enzmldoc.measurement_dict["m0"].getProtein("s0")
        meas_data.unit = "fmole / l"

        # On replicate level
        for replicate in meas_data.replicates:
            replicate.data_unit = "fmole / l"

        # Perform checkup in default - Should work
        is_consistent, report = EnzymeMLValidator.check_unit_consistency(
            enzmldoc, strict=False
        )

        assert is_consistent
        assert not report

        # Perform checkup in strict - Should fail
        is_consistent, report = EnzymeMLValidator.check_unit_consistency(
            enzmldoc, strict=True
        )

        assert not is_consistent
        assert report == {
            "conc_units": {
                "fmole / l": ["s0", "m0/s0", "m0/s0/repl_s0_0"],
                "mmole / l": ["p0", "m0/p0", "m0/p0/repl_p0_0", "s1", "c0"],
            },
            "volume_units": {
                "l": ["m0/p0", "m0/p0/repl_p0_0", "m0/s0", "m0/s0/repl_s0_0"],
                "ml": ["v0"],
            },
        }

    def test_check_unit_consistency_strict_mode_time(self, enzmldoc):
        """Test strict mode and change units for a parameter (should fail, default works)"""

        # Change time unit of a parameter
        param = enzmldoc.reaction_dict["r0"].model.parameters[0]
        param.unit = "1 / min"

        # Perform checkup in default - Should work
        is_consistent, report = EnzymeMLValidator.check_unit_consistency(
            enzmldoc, strict=False
        )

        assert is_consistent
        assert not report

        # Perform checkup in strict - Should fail
        is_consistent, report = EnzymeMLValidator.check_unit_consistency(
            enzmldoc, strict=True
        )

        assert not is_consistent
        assert report == {
            "time_units": {
                "min": ["x"],
                "s": ["m0/p0", "m0/p0/repl_p0_0", "m0/s0", "m0/s0/repl_s0_0"],
            },
            "volume_units": {
                "l": ["m0/p0", "m0/p0/repl_p0_0", "m0/s0", "m0/s0/repl_s0_0"],
                "ml": ["v0"],
            },
        }

    def test_check_unit_consistency_default_mode_negative(self, enzmldoc):
        """Test default mode and change units for a single species (both should fail)"""

        # Change the unit of a reactant
        reactant = enzmldoc.reactant_dict["s0"]
        reactant.unit = "fmole / l"

        # Perform checkup in default - Should work
        is_consistent, report = EnzymeMLValidator.check_unit_consistency(
            enzmldoc, strict=False
        )

        assert not is_consistent
        assert report == {
            "s0": {
                "measurements": {"m0": {"expected": "fmole / l", "given": "mmole / l"}},
                "replicates": {"m0": {"expected": "fmole / l", "given": "mmole / l"}},
            }
        }

        # Perform checkup in strict - Should fail
        is_consistent, report = EnzymeMLValidator.check_unit_consistency(
            enzmldoc, strict=True
        )

        assert not is_consistent
        assert report == {
            "s0": {
                "measurements": {"m0": {"expected": "fmole / l", "given": "mmole / l"}},
                "replicates": {"m0": {"expected": "fmole / l", "given": "mmole / l"}},
            },
            "conc_units": {
                "fmole / l": ["s0"],
                "mmole / l": [
                    "p0",
                    "m0/p0",
                    "m0/p0/repl_p0_0",
                    "m0/s0",
                    "m0/s0/repl_s0_0",
                    "s1",
                    "c0",
                ],
            },
            "volume_units": {
                "l": ["m0/p0", "m0/p0/repl_p0_0", "m0/s0", "m0/s0/repl_s0_0"],
                "ml": ["v0"],
            },
        }
