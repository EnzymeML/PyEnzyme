from pyenzyme.v1 import EnzymeMLDocument


class TestLegacy:
    """Test class for legacy functionality of EnzymeML v1."""

    def test_legacy(self):
        """Test that EnzymeML documents can be loaded from OMEX files and converted to XML.

        This test verifies backward compatibility by:
        1. Loading an EnzymeML document from an OMEX archive
        2. Converting it to XML string format
        3. Comparing the output with expected XML content

        The test ensures that the XML serialization process produces
        consistent and expected output for legacy OMEX files.
        """
        enzmldoc = EnzymeMLDocument.fromFile("tests/fixtures/sbml/v1_example.omex")
        expected = open("tests/fixtures/sbml/v1_sbml.xml", "r", encoding="utf-8").read()
        actual = enzmldoc.toXMLString()

        assert actual == expected
