import pytest

from pyenzyme.enzymeml.core.enzymereaction import EnzymeReaction, ReactionElement
from pyenzyme.enzymeml.core.ontology import SBOTerm
from pyenzyme.enzymeml.core.exceptions import SpeciesNotFoundError


class TestEnzymeReactionBasic:
    def test_content(self):
        """Test consistency of inputs"""

        reaction = EnzymeReaction(
            name="SomeReaction",
            reversible=True,
            temperature=100.0,
            temperature_unit="C",
            ph=7.0,
            ontology=SBOTerm.BIOCHEMICAL_REACTION,
            id="r0",
            meta_id="undefined",
            creator_id="a0",
            uri="URI",
            model=None,
        )

        assert reaction.name == "SomeReaction"
        assert reaction.reversible
        assert reaction.temperature == 100.0 + 273.15
        assert reaction.temperature_unit == "K"
        assert reaction.ph == 7.0
        assert reaction.ontology == SBOTerm.BIOCHEMICAL_REACTION
        assert reaction.id == "r0"
        assert reaction.meta_id == "METAID_R0"
        assert reaction.creator_id == "a0"
        assert reaction.uri == "URI"
        assert not reaction.model
        assert reaction.educts == []
        assert reaction.products == []
        assert reaction.modifiers == []

    def test_defaults(self):
        """Test if the defaults are the same"""

        reaction = EnzymeReaction(name="SomeReaction", reversible=True)

        assert not reaction.temperature
        assert not reaction.temperature_unit
        assert not reaction.ph
        assert not reaction.id
        assert not reaction.meta_id
        assert not reaction.uri
        assert not reaction.creator_id
        assert not reaction.model
        assert reaction.ontology == SBOTerm.BIOCHEMICAL_REACTION
        assert reaction.educts == []
        assert reaction.products == []
        assert reaction.modifiers == []

    def test_get_element(self, reaction):
        """Tests the element getter"""

        # Now apply the get methods
        educt = reaction.getEduct("s0")
        assert educt.species_id == "s0"
        assert educt.stoichiometry == 1.0
        assert educt.constant is False
        assert educt.ontology == SBOTerm.SUBSTRATE

        product = reaction.getProduct("s1")
        assert product.species_id == "s1"
        assert product.stoichiometry == 1.0
        assert product.constant is False
        assert product.ontology == SBOTerm.PRODUCT

        modifier = reaction.getModifier("p0")
        assert modifier.species_id == "p0"
        assert modifier.stoichiometry == 1.0
        assert modifier.constant is True
        assert modifier.ontology == SBOTerm.CATALYST

        # Test not existent identifiers
        with pytest.raises(SpeciesNotFoundError):
            reaction.getEduct("s100")
        with pytest.raises(SpeciesNotFoundError):
            reaction.getProduct("s100")
        with pytest.raises(SpeciesNotFoundError):
            reaction.getModifier("s100")

    def test_add_element(self, enzmldoc):
        """Tests the add methods"""

        # Fetch the reaction for testing and reset elements
        reaction = enzmldoc.reaction_dict["r0"]
        reaction.educts = []
        reaction.products = []
        reaction.modifiers = []

        # Test educt addition
        reaction.addEduct(
            species_id="s0", stoichiometry=1.0, constant=False, enzmldoc=enzmldoc
        )

        # Fetch the educt
        educt = reaction.getEduct("s0")
        assert educt.species_id == "s0"
        assert educt.stoichiometry == 1.0
        assert educt.constant is False
        assert educt.ontology == SBOTerm.SUBSTRATE

        # Test product addition
        reaction.addProduct(
            species_id="s1", stoichiometry=1.0, constant=False, enzmldoc=enzmldoc
        )

        # Fetch the educt
        product = reaction.getProduct("s1")
        assert product.species_id == "s1"
        assert product.stoichiometry == 1.0
        assert product.constant is False
        assert product.ontology == SBOTerm.PRODUCT

        # Test product addition
        reaction.addModifier(
            species_id="p0", stoichiometry=1.0, constant=False, enzmldoc=enzmldoc
        )

        # Fetch the educt
        modifier = reaction.getModifier("p0")
        assert modifier.species_id == "p0"
        assert modifier.stoichiometry == 1.0
        assert modifier.constant is False
        assert modifier.ontology == SBOTerm.CATALYST

        # Test case, ID not in document
        with pytest.raises(SpeciesNotFoundError):
            reaction.addEduct(
                species_id="s100", stoichiometry=1.0, constant=False, enzmldoc=enzmldoc
            )

        with pytest.raises(SpeciesNotFoundError):
            reaction.addProduct(
                species_id="s100", stoichiometry=1.0, constant=False, enzmldoc=enzmldoc
            )

        with pytest.raises(SpeciesNotFoundError):
            reaction.addModifier(
                species_id="s100", stoichiometry=1.0, constant=False, enzmldoc=enzmldoc
            )

    def test_from_equation_with_names(self, enzmldoc):
        """Tests initialization from equation using names"""

        # Test for irreversible case
        reaction = EnzymeReaction.fromEquation(
            "2.0 Reactant + Protein -> Complex",
            "SomeReaction",
            enzmldoc,
            temperature=100.0,
            temperature_unit="C",
            ph=7.0,
        )

        assert reaction.name == "SomeReaction"
        assert reaction.temperature == 100 + 273.15
        assert reaction.temperature_unit == "K"
        assert reaction.ph == 7.0
        assert reaction.reversible is False

        # Fetch the educt (should be s0)
        educt = reaction.getEduct("s0")
        assert educt.species_id == "s0"
        assert educt.stoichiometry == 2.0
        assert educt.constant is False
        assert educt.ontology == SBOTerm.SUBSTRATE

        # Fetch the educt (should be p0)
        product = reaction.getEduct("p0")
        assert product.species_id == "p0"
        assert product.stoichiometry == 1.0
        assert product.constant is False
        assert product.ontology == SBOTerm.SUBSTRATE

        # Fetch the product (should be c0)
        product = reaction.getProduct("c0")
        assert product.species_id == "c0"
        assert product.stoichiometry == 1.0
        assert product.constant is False
        assert product.ontology == SBOTerm.PRODUCT

        # Test for irreversible case
        reaction = EnzymeReaction.fromEquation(
            "2.0 Reactant + Protein = Complex",
            "SomeReaction",
            enzmldoc,
            temperature=100.0,
            temperature_unit="C",
            ph=7.0,
        )

        assert reaction.name == "SomeReaction"
        assert reaction.temperature == 100 + 273.15
        assert reaction.temperature_unit == "K"
        assert reaction.ph == 7.0
        assert reaction.reversible is True

        # Fetch the educt (should be s0)
        educt = reaction.getEduct("s0")
        assert educt.species_id == "s0"
        assert educt.stoichiometry == 2.0
        assert educt.constant is False
        assert educt.ontology == SBOTerm.SUBSTRATE

        # Fetch the educt (should be p0)
        product = reaction.getEduct("p0")
        assert product.species_id == "p0"
        assert product.stoichiometry == 1.0
        assert product.constant is False
        assert product.ontology == SBOTerm.SUBSTRATE

        # Fetch the product (should be c0)
        product = reaction.getProduct("c0")
        assert product.species_id == "c0"
        assert product.stoichiometry == 1.0
        assert product.constant is False
        assert product.ontology == SBOTerm.PRODUCT

    def test_from_equation_with_ids(self, enzmldoc):
        """Tests initialization from equation using names"""

        # Test for irreversible case
        reaction = EnzymeReaction.fromEquation(
            "2.0 s0 + p0 -> c0",
            "SomeReaction",
            enzmldoc,
            temperature=100.0,
            temperature_unit="C",
            ph=7.0,
        )

        assert reaction.name == "SomeReaction"
        assert reaction.temperature == 100 + 273.15
        assert reaction.temperature_unit == "K"
        assert reaction.ph == 7.0
        assert reaction.reversible is False

        # Fetch the educt (should be s0)
        educt = reaction.getEduct("s0")
        assert educt.species_id == "s0"
        assert educt.stoichiometry == 2.0
        assert educt.constant is False
        assert educt.ontology == SBOTerm.SUBSTRATE

        # Fetch the educt (should be p0)
        product = reaction.getEduct("p0")
        assert product.species_id == "p0"
        assert product.stoichiometry == 1.0
        assert product.constant is False
        assert product.ontology == SBOTerm.SUBSTRATE

        # Fetch the product (should be c0)
        product = reaction.getProduct("c0")
        assert product.species_id == "c0"
        assert product.stoichiometry == 1.0
        assert product.constant is False
        assert product.ontology == SBOTerm.PRODUCT

        # Test for irreversible case
        reaction = EnzymeReaction.fromEquation(
            "2.0 s0 + p0 = c0",
            "SomeReaction",
            enzmldoc,
            temperature=100.0,
            temperature_unit="C",
            ph=7.0,
        )

        assert reaction.name == "SomeReaction"
        assert reaction.temperature == 100 + 273.15
        assert reaction.temperature_unit == "K"
        assert reaction.ph == 7.0
        assert reaction.reversible is True

        # Fetch the educt (should be s0)
        educt = reaction.getEduct("s0")
        assert educt.species_id == "s0"
        assert educt.stoichiometry == 2.0
        assert educt.constant is False
        assert educt.ontology == SBOTerm.SUBSTRATE

        # Fetch the educt (should be p0)
        product = reaction.getEduct("p0")
        assert product.species_id == "p0"
        assert product.stoichiometry == 1.0
        assert product.constant is False
        assert product.ontology == SBOTerm.SUBSTRATE

        # Fetch the product (should be c0)
        product = reaction.getProduct("c0")
        assert product.species_id == "c0"
        assert product.stoichiometry == 1.0
        assert product.constant is False
        assert product.ontology == SBOTerm.PRODUCT

    def test_faulty_equation_init(self, enzmldoc):
        """Tests faulty instances of equation initialization"""

        # No arrow
        with pytest.raises(ValueError):
            EnzymeReaction.fromEquation("1.0 s0 + 2.0 p0", "FaultyReaction", enzmldoc)

        # No right side (irrev)
        with pytest.raises(ValueError):
            EnzymeReaction.fromEquation(
                "1.0 s0 + 2.0 p0 -> ", "FaultyReaction", enzmldoc
            )

        # No right side (rev)
        with pytest.raises(ValueError):
            EnzymeReaction.fromEquation(
                "1.0 s0 + 2.0 p0 = ", "FaultyReaction", enzmldoc
            )

        # No right side (irrev)
        with pytest.raises(ValueError):
            EnzymeReaction.fromEquation(
                " -> 1.0 s0 + 2.0 p0", "FaultyReaction", enzmldoc
            )

        # No right side (rev)
        with pytest.raises(ValueError):
            EnzymeReaction.fromEquation("= 1.0 s0 + 2.0 p0", "FaultyReaction", enzmldoc)

    def test_set_model(self, enzmldoc, correct_model, faulty_model):
        """Tests if the model is set correctly."""

        # Correct case
        reaction = enzmldoc.getReaction("r0")
        reaction.model = None

        # Set the model and check if the units are set correctly
        reaction.setModel(correct_model, enzmldoc)
        assert reaction.model.name == "SomeModel"
        assert reaction.model.equation == "s0 * x"

        # Check parameters are converted correctly
        parameter = reaction.model.parameters[0]
        assert parameter.name == "x"
        assert parameter.value == 10.0
        assert parameter.unit == "mmole / l"
        assert enzmldoc._unit_dict[parameter._unit_id].name == "mmole / l"

        # Faulty case
        with pytest.raises(SpeciesNotFoundError):
            reaction.setModel(faulty_model, enzmldoc)

    def test_get_stoich_coeffs(self, enzmldoc):
        """Tests if the method to return stoich coefficients works"""

        # Get the reaction
        reaction = enzmldoc.getReaction("r0")

        # Set the expected example and test against method
        correct_coeffs = {"s0": 1.0, "s1": -1.0}
        coeffs = reaction.getStoichiometricCoefficients()
        assert coeffs == correct_coeffs

    def test_initial_value_application(self, enzmldoc):
        """Tests whether initial values are applied correctly"""

        # Correct test case
        # Set up initial values and get reaction
        init_values = {
            "x": {"initial_value": 100.0, "upper": 200.0, "lower": 0, "constant": False}
        }
        reaction = enzmldoc.getReaction("r0")

        # Apply method and assert
        reaction.apply_initial_values(init_values)
        assert reaction.model.parameters[0].initial_value == 100.0

        # Test case with wrong identifier
        init_values = {"y": 100.0}
        with pytest.raises(KeyError):
            reaction.apply_initial_values(init_values)

        # Test case with unset model
        reaction.model = None
        with pytest.raises(ValueError):
            reaction.apply_initial_values(init_values)


class TestReactionElement:
    def test_content(self):
        """Tests consistency of content"""

        element = ReactionElement(
            species_id="s0", stoichiometry=1.0, constant=False, ontology=SBOTerm.PRODUCT
        )

        assert element.species_id == "s0"
        assert element.constant is False
        assert element.ontology == SBOTerm.PRODUCT
