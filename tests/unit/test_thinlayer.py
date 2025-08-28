from pyenzyme.thinlayers.base import BaseThinLayer
from pyenzyme.versions.v2 import EnzymeMLDocument, EquationType

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
        thinlayer = MockThinLayer(enzmldoc, remove_unmodeled_species=True)

        assert len(thinlayer.enzmldoc.small_molecules) == 2, (
            f"Unmodeled small molecules should be removed, but {len(thinlayer.enzmldoc.small_molecules)} remain."
        )
        assert len(thinlayer.enzmldoc.measurements) == 2, (
            f"Unmodeled measurements should be removed, but {len(thinlayer.enzmldoc.measurements)} remain."
        )

        measurement_has_unmodeled: list[str] = []

        for measurement in thinlayer.enzmldoc.measurements:
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
        thinlayer = MockThinLayer(enzmldoc, remove_unmodeled_species=True)

        assert len(thinlayer.enzmldoc.small_molecules) == 2, (
            f"Unmodeled small molecules should be removed, but {len(thinlayer.enzmldoc.small_molecules)} remain."
        )
        assert len(thinlayer.enzmldoc.measurements) == 2, (
            f"Unmodeled measurements should be removed, but {len(thinlayer.enzmldoc.measurements)} remain."
        )

        measurement_has_unmodeled: list[str] = []

        for measurement in thinlayer.enzmldoc.measurements:
            for species_data in measurement.species_data:
                if species_data.species_id == "Unmodeled":
                    measurement_has_unmodeled.append(measurement.id)

        assert len(measurement_has_unmodeled) == 0, (
            f"Unmodeled species should be removed, but appears in measurements {measurement_has_unmodeled}."
        )

    def test_leave_unmodeled_species(self):
        """
        Test that unmodeled species are preserved when remove_unmodeled_species=False.

        This test verifies that:
        - All species are kept in the document regardless of modeling status
        - Empty measurements are still removed
        - Measurements with unmodeled species are preserved
        """
        enzmldoc = self._create_enzmldoc()

        # Add reaction with only Substrate and Product (Unmodeled remains unmodeled)
        reaction = enzmldoc.add_to_reactions(id="R1", name="R1")
        reaction.add_to_reactants(species_id="Substrate", stoichiometry=1)
        reaction.add_to_products(species_id="Product", stoichiometry=1)

        # Keep unmodeled species
        thinlayer = MockThinLayer(enzmldoc, remove_unmodeled_species=False)

        assert len(thinlayer.enzmldoc.small_molecules) == 3, (
            f"Unmodeled small molecules should not be removed, but {len(thinlayer.enzmldoc.small_molecules)} remain."
        )

        assert len(thinlayer.enzmldoc.measurements) == 3, (
            f"Empty measurements should be removed, but {len(thinlayer.enzmldoc.measurements)} remain."
        )

        measurement_has_unmodeled: list[str] = []

        for measurement in thinlayer.enzmldoc.measurements:
            for species_data in measurement.species_data:
                if species_data.species_id == "Unmodeled":
                    measurement_has_unmodeled.append(measurement.id)

        assert len(measurement_has_unmodeled) == 2, (
            f"Unmodeled species should not be removed, but appears in measurements {measurement_has_unmodeled}."
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
        unmodeled = enzmldoc.add_to_small_molecules(id="Unmodeled", name="Unmodeled")

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
        pass

    def write(self, *args, **kwargs):
        """Mock write method that does nothing."""
        pass
