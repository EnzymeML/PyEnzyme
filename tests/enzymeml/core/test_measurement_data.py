import pytest

from pyenzyme.enzymeml.core.measurementData import MeasurementData
from pyenzyme.enzymeml.core.exceptions import MeasurementDataSpeciesIdentifierError


class TestMeasurementData:
    def test_content(self):
        """Tests data consistency"""

        # Check for reactant input
        data = MeasurementData(
            init_conc=10.0, unit="mmole / l", measurement_id="m0", reactant_id="s0"
        )

        assert data.init_conc == 10.0
        assert data.unit == "mmole / l"
        assert data.measurement_id == "m0"
        assert data.reactant_id == "s0"
        assert not data.protein_id
        assert not data.replicates

        # Check for protein input
        data = MeasurementData(
            init_conc=10.0, unit="mmole / l", measurement_id="m0", protein_id="p0"
        )

        assert data.init_conc == 10.0
        assert data.unit == "mmole / l"
        assert data.measurement_id == "m0"
        assert data.protein_id == "p0"
        assert not data.reactant_id
        assert not data.replicates

    def test_false_ids(self):
        """Tests the cases when either no or both IDs are given"""

        # Check when both are not given
        with pytest.raises(MeasurementDataSpeciesIdentifierError):
            MeasurementData(init_conc=10.0, unit="mmole / l", measurement_id="m0")

        # Check when both are given at same time
        with pytest.raises(MeasurementDataSpeciesIdentifierError):
            MeasurementData(
                init_conc=10.0,
                unit="mmole / l",
                measurement_id="m0",
                reactant_id="s0",
                protein_id="p0",
            )

    def test_unify_units(self, enzmldoc):
        """Tests the rescaling of units"""

        # Fetch the measurement data object
        measurement = enzmldoc.measurement_dict["m0"]
        data = measurement.species_dict["reactants"]["s0"]

        # Apply unifyUnits method and get the replicate
        data.unifyUnits(kind="mole", scale=-6, enzmldoc=enzmldoc)
        replicate = data.replicates[0]

        assert replicate.data == [1000.0, 1000.0, 1000.0, 1000.0]
        assert replicate.data_unit == "umole / l"
        assert enzmldoc._unit_dict[replicate._data_unit_id].name == "umole / l"

        assert data.init_conc == 10000.0
        assert data.unit == "umole / l"

    def test_add_replicate(self, measurement, replicate):
        """Tests if the added replicate is correct"""

        # Reset objects replicates
        data = measurement.species_dict["reactants"]["s0"]
        data.replicates = []

        # Apply method
        data.addReplicate(replicate)

        assert data.replicates == [replicate]
