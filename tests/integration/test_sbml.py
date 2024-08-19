from pathlib import Path

from pyenzyme import EnzymeMLDocument
from pyenzyme.tools import to_dict_wo_json_ld


class TestSBML:
    def test_parse_sbml_odes(self):
        # Arrange
        path = Path("tests/fixtures/sbml/odes_example.omex")

        # Act
        enzmldoc = EnzymeMLDocument.from_sbml(path)

        # Assert
        parsed_doc = to_dict_wo_json_ld(enzmldoc)
        expected_doc = to_dict_wo_json_ld(
            EnzymeMLDocument.read("tests/fixtures/sbml/ode_example_enzml.json")
        )

        assert (
            parsed_doc == expected_doc
        ), "Parsed document does not match expected document"

    def test_parse_sbml_reactions(self):
        # Arrange
        path = Path("tests/fixtures/sbml/reactions_example.omex")

        # Act
        enzmldoc = EnzymeMLDocument.from_sbml(path)

        # Assert
        parsed_doc = to_dict_wo_json_ld(enzmldoc)
        expected_doc = to_dict_wo_json_ld(
            EnzymeMLDocument.read("tests/fixtures/sbml/reaction_example_enzml.json")
        )

        assert (
            parsed_doc == expected_doc
        ), "Parsed document does not match expected document"
