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
