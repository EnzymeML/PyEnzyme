import json

from pyenzyme.enzymeml.core.enzymemldocument import EnzymeMLDocument


class TestTemplateReader:
    def test_template_conversion(self, template_example):
        """Tests the conversion of the EnzymeML Spreadsheet template"""

        # Convert the template fixture
        enzmldoc = EnzymeMLDocument.fromTemplate(
            "./tests/fixtures/EnzymeML_Template_Example.xlsm"
        )

        assert json.loads(enzmldoc.json()) == template_example
