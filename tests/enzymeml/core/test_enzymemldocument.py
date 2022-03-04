import os

from pyenzyme.enzymeml.core.enzymemldocument import EnzymeMLDocument
from pyenzyme.enzymeml.core.abstract_classes import AbstractSpecies
from pyenzyme.enzymeml.core.ontology import SBOTerm


class TestEnzymeMLDocument:
    def test_content(self):
        """Tests if content that is inserted is consistent"""

        # Create an instance
        enzmldoc = EnzymeMLDocument(
            name="Test",
            level=3,
            version=2,
            pubmedid="91245",
            url="http://www.example.com",
            doi="10.1109/5.771073",
            created="01-02-1991",
            modified="01-02-1996",
        )

        assert enzmldoc.name == "Test"
        assert enzmldoc.level == 3
        assert enzmldoc.version == 2
        assert enzmldoc.pubmedid == "https://identifiers.org/pubmed:91245"
        assert enzmldoc.url == "http://www.example.com"
        assert enzmldoc.doi == "10.1109/5.771073"
        assert enzmldoc.created == "01-02-1991"
        assert enzmldoc.modified == "01-02-1996"
        assert not enzmldoc.creator_dict
        assert not enzmldoc.vessel_dict
        assert not enzmldoc.protein_dict
        assert not enzmldoc.complex_dict
        assert not enzmldoc.reactant_dict
        assert not enzmldoc.reaction_dict
        assert not enzmldoc.unit_dict
        assert not enzmldoc.file_dict
        assert not enzmldoc.global_parameters

    def test_defaults(self):
        """Tests if all default values are correct"""

        # Create an instance
        enzmldoc = EnzymeMLDocument(name="Test")

        assert enzmldoc.name == "Test"
        assert enzmldoc.level == 3
        assert enzmldoc.version == 2
        assert not enzmldoc.pubmedid
        assert not enzmldoc.url
        assert not enzmldoc.doi
        assert not enzmldoc.created
        assert not enzmldoc.modified
        assert not enzmldoc.creator_dict
        assert not enzmldoc.vessel_dict
        assert not enzmldoc.protein_dict
        assert not enzmldoc.complex_dict
        assert not enzmldoc.reactant_dict
        assert not enzmldoc.reaction_dict
        assert not enzmldoc.unit_dict
        assert not enzmldoc.file_dict
        assert not enzmldoc.global_parameters

    def test_from_file_init(self, enzmldoc):
        """Tests initialization from file"""

        # Read the OMEX fixture
        result = EnzymeMLDocument.fromFile("./tests/fixtures/test_case.omex")

        # Test if its JSON representation matches
        assert result.dict(exclude={"log"}) == enzmldoc.dict(exclude={"log"})

    def test_from_json_init(self):
        """Tests initialization from a JSON string"""

        # Read the expected OMEX output
        expected = EnzymeMLDocument.fromFile("./tests/fixtures/test_case.omex")

        # Read the JSON equivalent
        result = EnzymeMLDocument.fromJSON(
            open("./tests/fixtures/enzmldoc_object.json").read()
        )

        assert expected.dict(exclude={"log"}) == result.dict(exclude={"log"})

    def test_to_file(self, enzmldoc):
        """Tests writing to a file"""

        # Store the expection to later compare
        expected = enzmldoc.dict(exclude={"log"})

        # Write to a file and check existence
        enzmldoc.toFile("./tests/", name="write_test")
        assert os.path.exists("./tests/write_test.omex")

        # Read the resulting file and compare the content
        result = EnzymeMLDocument.fromFile("./tests/write_test.omex")
        assert result.dict(exclude={"log"}) == expected

    def test_add_global_params(self):
        """Tests the addition of a global parameter"""

        # Initialize an object
        enzmldoc = EnzymeMLDocument(name="Test")

        # Add a Parameter
        enzmldoc.addGlobalParameter(
            name="GlobalParam",
            value=100.0,
            initial_value=100.0,
            unit="mmole / l",
            constant=False,
            lower=0.0,
            upper=200.0,
            stdev=0.001,
        )

        assert "GlobalParam" in enzmldoc.global_parameters

        # Get the parameter an check values
        param = enzmldoc.global_parameters["GlobalParam"]

        assert param.name == "GlobalParam"
        assert param.value == 100.0
        assert param.unit == "mmole / l"
        assert param.constant is False
        assert param.lower == 0.0
        assert param.upper == 200.0
        assert param.stdev == 0.001
        assert param.is_global is True

    def test_add_species(self):
        """Tests the addition of a species"""

        # Initialize object
        enzmldoc = EnzymeMLDocument(name="Test")

        # Use the abstract function and an abstract type to test
        test_class = type("Species", (AbstractSpecies,), {"unit": "mmole / l"})
        species = test_class(
            name="TestSpecies",
            vessel_id="v0",
            constant=True,
            boundary=True,
            ontology=SBOTerm.PROTEIN,
        )

        # Finally add the species
        enzmldoc._addSpecies(species, prefix="p", dictionary=enzmldoc.protein_dict)

        assert "p0" in enzmldoc.protein_dict
        assert species == enzmldoc.protein_dict["p0"]
