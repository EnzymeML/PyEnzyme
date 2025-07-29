import pytest

from pyenzyme.equations.chem import build_reaction, build_reactions
from pyenzyme.equations.math import build_equation, build_equations
from pyenzyme import EquationType, EnzymeMLDocument


class TestMathEquations:
    def test_parse_equation(self):
        # Arrange
        enzmldoc = EnzymeMLDocument(name="Test")
        enzmldoc.add_to_proteins(id="p0", name="Protein 0")
        enzmldoc.add_to_small_molecules(id="s0", name="Species 0")

        equation = "s1'(t) = kcat * p0 * s0"

        # Act
        equation = build_equation(
            equation=equation,
            unit_mapping={"kcat": "1 / s"},
            enzmldoc=enzmldoc,
        )

        # Assert
        expected_vars = ["p0", "s0"]
        expected_params = ["kcat"]

        assert equation.species_id == "s1", (
            f"Species ID is not correct. Got {equation.species_id}"
        )
        assert equation.equation == "kcat*p0*s0", (
            "Equation is not correct. Got {equation.equation.equation}"
        )

        for var in equation.variables:
            assert var.name in expected_vars
            assert var.symbol in expected_vars

        for param in enzmldoc.parameters:
            assert param.name in expected_params
            assert param.symbol in expected_params
            assert param.id in expected_params
            assert param.unit is not None

    def test_invalid_equation_no_right(self):
        # Arrange
        enzmldoc = EnzymeMLDocument(name="Test")
        equation = "s1'(t) ="

        # Act
        with pytest.raises(ValueError):
            build_equation(
                equation=equation,
                unit_mapping={"kcat": "1 / s"},
                enzmldoc=enzmldoc,
            )

    def test_invalid_equation_no_equals(self):
        # Arrange
        enzmldoc = EnzymeMLDocument(name="Test")
        equation = "s1'(t) kcat * p0(t) * s0(t)"

        # Act
        with pytest.raises(ValueError):
            build_equation(
                equation=equation,
                unit_mapping={"kcat": "1 / s"},
                enzmldoc=enzmldoc,
            )

    def test_equation_with_funs(self):
        # Arrange
        enzmldoc = EnzymeMLDocument(name="Test")
        equation = "s1'(t) = kcat * exp(p0(t) * t)"

        # Act
        equation = build_equation(
            equation=equation,
            unit_mapping={"kcat": "1 / s"},
            enzmldoc=enzmldoc,
        )

        # Assert
        assert equation.species_id == "s1", (
            f"Species ID is not correct. Got {equation.species_id}"
        )
        assert equation.equation == "kcat*exp(p0*t)", (
            f"Equation is not correct. Got {equation.equation}"
        )

    def test_equation_with_fun_only_t(self):
        # Arrange
        enzmldoc = EnzymeMLDocument(name="Test")
        equation = "s1'(t) = kcat * exp(t)"

        # Act
        equation = build_equation(
            equation=equation,
            unit_mapping={"kcat": "1 / s"},
            enzmldoc=enzmldoc,
        )

        # Assert
        assert equation.species_id == "s1", (
            f"Species ID is not correct. Got {equation.species_id}"
        )
        assert equation.equation == "kcat*exp(t)", (
            f"Equation is not correct. Got {equation.equation}"
        )

    def test_multiple_equations(self):
        # Arrange
        enzmldoc = EnzymeMLDocument(name="Test")
        equations = [
            "s1'(t) = kcat * E_tot * s0(t)",
            "E_tot = p0(t) + p1(t)",
        ]

        # Act
        equations = build_equations(
            *equations,
            unit_mapping={"kcat": "1 / s"},
            enzmldoc=enzmldoc,
        )

        # Assert
        assert len(equations) == 2, f"Expected 2 equations. Got {len(equations)}"

    def test_init_assigment_equation(self):
        # Arrange
        enzmldoc = EnzymeMLDocument(name="Test")
        equation = "E_tot = p0 + p1"

        # Act
        equation = build_equation(
            equation,
            enzmldoc=enzmldoc,
        )

        # Assert
        assert equation.species_id == "E_tot", (
            f"Species ID is not correct. Got {equation.species_id}"
        )
        assert equation.equation == "p0 + p1", (
            f"Equation is not correct. Got {equation.equation}"
        )
        assert equation.equation_type == EquationType.INITIAL_ASSIGNMENT, (
            f"Equation type is not correct. Got {equation.equation_type}"
        )

    def test_assigment_equation(self):
        # Arrange
        enzmldoc = EnzymeMLDocument(name="Test")
        equation = "E_tot(t) = p0 + p1"

        # Act
        equation = build_equation(
            equation=equation,
            enzmldoc=enzmldoc,
        )

        # Assert
        assert equation.species_id == "E_tot", (
            f"Species ID is not correct. Got {equation.species_id}"
        )
        assert equation.equation == "p0 + p1", (
            f"Equation is not correct. Got {equation.equation}"
        )
        assert equation.equation_type == EquationType.ASSIGNMENT, (
            f"Equation type is not correct. Got {equation.equation_type}"
        )


class TestChemEqautions:
    def test_build_irrev_reaction(self):
        # Arrange
        reaction_str = "2 s1 + s2 -> 2 s3 + s4"

        # Act
        reac = build_reaction(
            id="R1",
            name="Reaction 1",
            scheme=reaction_str,
        )

        # Assert
        expected_reactants = [
            (2.0, "s1"),
            (1.0, "s2"),
        ]

        expected_products = [
            (2.0, "s3"),
            (1.0, "s4"),
        ]

        assert reac.id == "R1", f"Reaction ID is not correct. Got {reac.id}"
        assert reac.name == "Reaction 1", (
            f"Reaction name is not correct. Got {reac.name}"
        )

        for stoich, species in expected_reactants:
            element = next(
                filter(lambda x: x.species_id == species, reac.reactants), None
            )

            if not element:
                assert False, f"Species {species} not found in reaction"

            assert element.stoichiometry == stoich, (
                f"Stoichiometry for {species} is not correct. Got {element.stoichiometry}"
            )

            assert element.species_id == species, (
                f"Species ID for {species} is not correct. Got {element.species_id}"
            )

        for stoich, species in expected_products:
            element = next(
                filter(lambda x: x.species_id == species, reac.products), None
            )

            if not element:
                assert False, f"Species {species} not found in reaction"

            assert element.stoichiometry == stoich, (
                f"Stoichiometry for {species} is not correct. Got {element.stoichiometry}"
            )

    def test_build_rev_reaction(self):
        # Arrange
        reaction_str = "s1 + s2 <=> s3 + s4"

        # Act
        reac = build_reaction(
            id="R1",
            name="Reaction 1",
            scheme=reaction_str,
        )

        # Assert
        assert reac.reversible is True, "Reaction is not reversible"

    def test_build_w_modifiers(self):
        # Arrange
        reaction_str = "s1 + s2 -> s3 + s4"

        # Act
        reac = build_reaction(
            id="R1",
            name="Reaction 1",
            scheme=reaction_str,
            modifiers=["s5", "s6"],
        )

        # Assert
        assert len(reac.modifiers) == 2, (
            f"Expected 2 modifiers. Got {len(reac.modifiers)}"
        )

    def test_build_invalid_reaction(self):
        # Arrange
        reaction_str = "s1 + s2 + s3"

        # Act
        with pytest.raises(ValueError):
            build_reaction("R1", "Reaction 1", reaction_str)

    def test_build_multiple_reactions(self):
        # Arrange
        reactions = [
            "s1 + s2 -> s3 + s4",
            "s2 -> s5",
        ]

        # Act
        reacs = build_reactions(*reactions)

        # Assert
        assert len(reacs) == 2, f"Expected 2 reactions. Got {len(reacs)}"

    def test_build_multiple_reactions_w_modifiers(self):
        # Arrange
        reactions = [
            "s1 + s2 -> s3 + s4",
            "s2 -> s5",
        ]

        # Act
        modifiers = {"r1": ["p0"]}
        reacs = build_reactions(*reactions, modifiers=modifiers)

        # Assert
        assert len(reacs) == 2, f"Expected 2 reactions. Got {len(reacs)}"

        r0 = reacs[0]
        assert len(r0.modifiers) == 1, f"Expected 1 modifier. Got {len(r0.modifiers)}"

        r1 = reacs[1]
        assert len(r1.modifiers) == 0, f"Expected 0 modifiers. Got {len(r1.modifiers)}"
