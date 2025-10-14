from pyenzyme.thinlayers.base import BaseThinLayer
from pyenzyme.versions.v2 import EnzymeMLDocument, Equation, EquationType

# Mock data for creating test species measurements
MOCK_DATA = {
    "initial": 1.0,
    "time": [1.0, 2.0, 3.0, 4.0],
    "data": [1.0, 2.0, 3.0, 4.0],
}


class TestThinLayer:
    """Test suite for BaseThinLayer functionality."""

    def test_remove_unmodeled_species_reaction(self):
        """
        Test that unmodeled species are removed when they're not part of any reaction.

        This test verifies that:
        - Species not referenced in reactions are removed from the document
        - Measurements containing only unmodeled species are removed
        - Measurements with mixed modeled/unmodeled species keep only modeled ones
        """
        enzmldoc = self._create_enzmldoc()

        # Add reaction with only Substrate and Product (Unmodeled is not included)
        reaction = enzmldoc.add_to_reactions(id="R1", name="R1")
        reaction.add_to_reactants(species_id="Substrate", stoichiometry=1)
        reaction.add_to_products(species_id="Product", stoichiometry=1)

        # Remove unmodeled species
        thinlayer = MockThinLayer(enzmldoc)
        tl_enzmldoc = thinlayer.optimize()

        assert len(tl_enzmldoc.small_molecules) == 2, (
            f"Unmodeled small molecules should be removed, but {len(tl_enzmldoc.small_molecules)} remain."
        )
        assert len(tl_enzmldoc.measurements) == 2, (
            f"Unmodeled measurements should be removed, but {len(tl_enzmldoc.measurements)} remain."
        )

        measurement_has_unmodeled: list[str] = []

        for measurement in tl_enzmldoc.measurements:
            for species_data in measurement.species_data:
                if species_data.species_id == "Unmodeled":
                    measurement_has_unmodeled.append(measurement.id)

        assert len(measurement_has_unmodeled) == 0, (
            f"Unmodeled species should be removed, but appears in measurements {measurement_has_unmodeled}."
        )

    def test_remove_unmodeled_species_odes(self):
        """
        Test that unmodeled species are removed when they're not part of any ODE.

        This test verifies that:
        - Species not referenced in ODE equations are removed from the document
        - Measurements containing only unmodeled species are removed
        - Measurements with mixed modeled/unmodeled species keep only modeled ones
        """
        enzmldoc = self._create_enzmldoc()

        # Add ODEs with only Substrate and Product (Unmodeled is not included)
        enzmldoc.add_to_equations(
            species_id="Substrate",
            equation_type=EquationType.ODE,
            equation="-Substrate",
        )

        enzmldoc.add_to_equations(
            species_id="Product",
            equation_type=EquationType.ODE,
            equation="Substrate",
        )

        # Remove unmodeled species
        thinlayer = MockThinLayer(enzmldoc)
        tl_enzmldoc = thinlayer.optimize()

        assert len(tl_enzmldoc.small_molecules) == 2, (
            f"Unmodeled small molecules should be removed, but {len(tl_enzmldoc.small_molecules)} remain."
        )
        assert len(tl_enzmldoc.measurements) == 2, (
            f"Unmodeled measurements should be removed, but {len(tl_enzmldoc.measurements)} remain."
        )

        measurement_has_unmodeled: list[str] = []

        for measurement in tl_enzmldoc.measurements:
            for species_data in measurement.species_data:
                if species_data.species_id == "Unmodeled":
                    measurement_has_unmodeled.append(measurement.id)

        assert len(measurement_has_unmodeled) == 0, (
            f"Unmodeled species should be removed, but appears in measurements {measurement_has_unmodeled}."
        )

    def test_includes_species_in_ode_equation(self):
        """
        Test that species referenced in equations are kept in the document even when
        they are not defined as ODEs or part of reactions.

        This test verifies that:
        - A species that appears in an equation (but not in reactions or ODEs) is kept
        - The species can have initial values in measurements without time course data
        - The filtering function correctly identifies equation-referenced species as modeled
        """
        enzmldoc = self._create_enzmldoc()

        # Add a new species that will only appear in equations (not reactions/ODEs)
        equation_only_species = enzmldoc.add_to_small_molecules(
            id="p1",
            name="Equation Only Species",
        )

        # Add an initial for the species to each measurement
        for i, measurement in enumerate(enzmldoc.measurements):
            measurement.add_to_species_data(
                species_id=equation_only_species.id,
                initial=i * 2.0,
                data=[],
                time=[],
            )

        # Add an assignment equation that references this species
        # This species is NOT an ODE and NOT part of any reaction
        enzmldoc.add_to_equations(
            species_id="Product",  # Left side of equation
            equation_type=EquationType.ODE,
            equation="p1 * 2.0",  # p1 appears in the equation
        )

        # Verify the species exists before filtering
        assert equation_only_species.id in [s.id for s in enzmldoc.small_molecules]

        # Remove unmodeled species
        thinlayer = MockThinLayer(enzmldoc)
        tl_enzmldoc = thinlayer.optimize()

        assert equation_only_species.id in [
            s.id for s in tl_enzmldoc.small_molecules
        ], (
            f"Species '{equation_only_species.id}' should be kept because it appears in an equation, "
            f"but it was removed. Remaining species: {[s.id for s in tl_enzmldoc.small_molecules]}"
        )

    def test_includes_species_in_assignment_equation(self):
        """
        Test that species referenced in equations are kept in the document even when
        they are not defined as ODEs or part of reactions.

        This test verifies that:
        - A species that appears in an equation (but not in reactions or ODEs) is kept
        - The species can have initial values in measurements without time course data
        - The filtering function correctly identifies equation-referenced species as modeled
        """
        enzmldoc = self._create_enzmldoc()

        # Add a new species that will only appear in equations (not reactions/ODEs)
        equation_only_species = enzmldoc.add_to_small_molecules(
            id="p1",
            name="Equation Only Species",
        )

        # Add an initial for the species to each measurement
        for i, measurement in enumerate(enzmldoc.measurements):
            measurement.add_to_species_data(
                species_id=equation_only_species.id,
                initial=i * 2.0,
                data=[],
                time=[],
            )

        # Add an assignment equation that references this species
        # This species is NOT an ODE and NOT part of any reaction
        enzmldoc.add_to_equations(
            species_id="Product",  # Left side of equation
            equation_type=EquationType.ASSIGNMENT,
            equation="p1 * 2.0",  # p1 appears in the equation
        )

        # Verify the species exists before filtering
        assert equation_only_species.id in [s.id for s in enzmldoc.small_molecules]

        # Remove unmodeled species
        thinlayer = MockThinLayer(enzmldoc)
        tl_enzmldoc = thinlayer.optimize()

        assert equation_only_species.id in [
            s.id for s in tl_enzmldoc.small_molecules
        ], (
            f"Species '{equation_only_species.id}' should be kept because it appears in an equation, "
            f"but it was removed. Remaining species: {[s.id for s in tl_enzmldoc.small_molecules]}"
        )

    def test_includes_species_in_initial_assignment_equation(self):
        """
        Test that species referenced in equations are kept in the document even when
        they are not defined as ODEs or part of reactions.

        This test verifies that:
        - A species that appears in an equation (but not in reactions or ODEs) is kept
        - The species can have initial values in measurements without time course data
        - The filtering function correctly identifies equation-referenced species as modeled
        """
        enzmldoc = self._create_enzmldoc()

        # Add a new species that will only appear in equations (not reactions/ODEs)
        equation_only_species = enzmldoc.add_to_small_molecules(
            id="p1",
            name="Equation Only Species",
        )

        # Add an initial for the species to each measurement
        for i, measurement in enumerate(enzmldoc.measurements):
            measurement.add_to_species_data(
                species_id=equation_only_species.id,
                initial=i * 2.0,
                data=[],
                time=[],
            )

        # Add an assignment equation that references this species
        # This species is NOT an ODE and NOT part of any reaction
        enzmldoc.add_to_equations(
            species_id="Product",  # Left side of equation
            equation_type=EquationType.INITIAL_ASSIGNMENT,
            equation="p1 * 2.0",  # p1 appears in the equation
        )

        # Verify the species exists before filtering
        assert equation_only_species.id in [s.id for s in enzmldoc.small_molecules]

        # Remove unmodeled species
        thinlayer = MockThinLayer(enzmldoc)
        tl_enzmldoc = thinlayer.optimize()

        assert equation_only_species.id in [
            s.id for s in tl_enzmldoc.small_molecules
        ], (
            f"Species '{equation_only_species.id}' should be kept because it appears in an equation, "
            f"but it was removed. Remaining species: {[s.id for s in tl_enzmldoc.small_molecules]}"
        )

    def test_includes_species_in_kinetic_law_equation(self):
        """
        Test that species referenced in equations are kept in the document even when
        they are not defined as ODEs or part of reactions.

        This test verifies that:
        - A species that appears in an equation (but not in reactions or ODEs) is kept
        - The species can have initial values in measurements without time course data
        - The filtering function correctly identifies equation-referenced species as modeled
        """
        enzmldoc = self._create_enzmldoc()

        # Add a new species that will only appear in equations (not reactions/ODEs)
        equation_only_species = enzmldoc.add_to_small_molecules(
            id="p1",
            name="Equation Only Species",
        )

        # Add an initial for the species to each measurement
        for i, measurement in enumerate(enzmldoc.measurements):
            measurement.add_to_species_data(
                species_id=equation_only_species.id,
                initial=i * 2.0,
                data=[],
                time=[],
            )

        # Add a reaction that references this species
        # This species is NOT an ODE and NOT part of any reaction
        reaction = enzmldoc.add_to_reactions(id="R1", name="R1")
        reaction.add_to_reactants(species_id="Substrate", stoichiometry=1)
        reaction.add_to_products(species_id="Product", stoichiometry=1)
        reaction.kinetic_law = Equation(
            equation="p1 * 2.0",
            equation_type=EquationType.RATE_LAW,
            species_id="v",
        )

        # Verify the species exists before filtering
        assert equation_only_species.id in [s.id for s in enzmldoc.small_molecules]

        # Remove unmodeled species
        thinlayer = MockThinLayer(enzmldoc)
        tl_enzmldoc = thinlayer.optimize()

        assert equation_only_species.id in [
            s.id for s in tl_enzmldoc.small_molecules
        ], (
            f"Species '{equation_only_species.id}' should be kept because it appears in a reaction, "
            f"but it was removed. Remaining species: {[s.id for s in tl_enzmldoc.small_molecules]}"
        )

    def _create_enzmldoc(self) -> EnzymeMLDocument:
        """
        Create a test EnzymeML document with various measurement scenarios.

        Creates a document with:
        - Three species: Substrate, Product, and Unmodeled
        - Four measurements:
          - M1: Contains all three species (mixed modeled/unmodeled)
          - M2: Contains only modeled species (Substrate, Product)
          - M3: Contains only unmodeled species (Unmodeled)
          - M4: Empty measurement (no species data)

        Returns:
            EnzymeMLDocument: A test document for use in unit tests.
        """
        enzmldoc = EnzymeMLDocument(name="Test")

        # Add small molecules
        substrate = enzmldoc.add_to_small_molecules(id="Substrate", name="Substrate")
        product = enzmldoc.add_to_small_molecules(id="Product", name="Product")
        unmodeled = enzmldoc.add_to_small_molecules(id="s1", name="Unmodeled")

        # Add a measurement with unmodeled species
        measurement = enzmldoc.add_to_measurements(id="M1", name="M1")
        measurement.add_to_species_data(species_id=substrate.id, **MOCK_DATA)
        measurement.add_to_species_data(species_id=product.id, **MOCK_DATA)
        measurement.add_to_species_data(species_id=unmodeled.id, **MOCK_DATA)

        # Add a Measurement only with modeled species
        measurement = enzmldoc.add_to_measurements(id="M2", name="M2")
        measurement.add_to_species_data(species_id=substrate.id, **MOCK_DATA)
        measurement.add_to_species_data(species_id=product.id, **MOCK_DATA)

        # Add a Measurement with only unmodeled species
        measurement = enzmldoc.add_to_measurements(id="M3", name="M3")
        measurement.add_to_species_data(species_id=unmodeled.id, **MOCK_DATA)

        # Add an empty measurement
        measurement = enzmldoc.add_to_measurements(id="M4", name="M4")

        return enzmldoc


class MockThinLayer(BaseThinLayer):
    """
    Mock implementation of BaseThinLayer for testing purposes.

    This class provides minimal implementations of the abstract methods
    to allow testing of the base class functionality without requiring
    a full thin layer implementation.
    """

    def integrate(self, *args, **kwargs):
        """Mock integration method that does nothing."""
        pass

    def optimize(self, *args, **kwargs):
        """Mock optimization method that does nothing."""
        return self._remove_unmodeled_species(self.enzmldoc)

    def write(self, *args, **kwargs):
        """Mock write method that does nothing."""
        pass
