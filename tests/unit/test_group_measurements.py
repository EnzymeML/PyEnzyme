from unittest.mock import Mock

from pyenzyme.tools import (
    _conditions_to_hashable,
    _get_measurement_conditions,
    group_measurements,
)


class TestGetMeasurementConditions:
    """Test suite for _get_measurement_conditions function"""

    def test_with_prepared_values(self):
        """Test extracting conditions from measurement with prepared values"""
        # Arrange
        species_data = [
            Mock(species_id="s1", prepared=10.0, initial=None),
            Mock(species_id="s2", prepared=5.0, initial=None),
        ]
        measurement = Mock(species_data=species_data, ph=7.4, temperature=25.0)

        # Act
        conditions = _get_measurement_conditions(measurement)

        # Assert
        expected = {"s1": 10.0, "s2": 5.0, "ph": 7.4, "temperature": 25.0}
        assert conditions == expected

    def test_with_initial_values(self):
        """Test extracting conditions from measurement with initial values"""
        # Arrange
        species_data = [
            Mock(species_id="s1", prepared=None, initial=8.0),
            Mock(species_id="s2", prepared=None, initial=3.0),
        ]
        measurement = Mock(species_data=species_data, ph=6.8, temperature=30.0)

        # Act
        conditions = _get_measurement_conditions(measurement)

        # Assert
        expected = {"s1": 8.0, "s2": 3.0, "ph": 6.8, "temperature": 30.0}
        assert conditions == expected

    def test_prepared_takes_precedence_over_initial(self):
        """Test that prepared values take precedence over initial values"""
        # Arrange
        species_data = [
            Mock(species_id="s1", prepared=15.0, initial=10.0),
            Mock(species_id="s2", prepared=None, initial=5.0),
        ]
        measurement = Mock(species_data=species_data, ph=None, temperature=None)

        # Act
        conditions = _get_measurement_conditions(measurement)

        # Assert
        expected = {
            "s1": 15.0,  # prepared value used
            "s2": 5.0,  # initial value used since prepared is None
        }
        assert conditions == expected

    def test_with_no_concentration_values(self):
        """Test with species data having no prepared or initial values"""
        # Arrange
        species_data = [
            Mock(species_id="s1", prepared=None, initial=None),
            Mock(species_id="s2", prepared=12.0, initial=None),
        ]
        measurement = Mock(species_data=species_data, ph=7.0, temperature=None)

        # Act
        conditions = _get_measurement_conditions(measurement)

        # Assert
        expected = {
            "s2": 12.0,  # only s2 included since s1 has no values
            "ph": 7.0,
        }
        assert conditions == expected

    def test_with_no_environmental_conditions(self):
        """Test with measurement having no pH or temperature"""
        # Arrange
        species_data = [
            Mock(species_id="enzyme", prepared=1.0, initial=None),
        ]
        measurement = Mock(species_data=species_data, ph=None, temperature=None)

        # Act
        conditions = _get_measurement_conditions(measurement)

        # Assert
        expected = {
            "enzyme": 1.0,
        }
        assert conditions == expected

    def test_with_empty_species_data(self):
        """Test with measurement having no species data"""
        # Arrange
        measurement = Mock(species_data=[], ph=7.5, temperature=37.0)

        # Act
        conditions = _get_measurement_conditions(measurement)

        # Assert
        expected = {"ph": 7.5, "temperature": 37.0}
        assert conditions == expected


class TestConditionsToHashable:
    """Test suite for _conditions_to_hashable function"""

    def test_with_normal_conditions(self):
        """Test converting normal conditions dict to hashable tuple"""
        # Arrange
        conditions = {"s1": 10.0, "ph": 7.4, "temperature": 25.0, "s2": 5.0}

        # Act
        hashable = _conditions_to_hashable(conditions)

        # Assert
        expected = (("ph", 7.4), ("s1", 10.0), ("s2", 5.0), ("temperature", 25.0))
        assert hashable == expected
        assert isinstance(hashable, tuple)

    def test_with_empty_conditions(self):
        """Test converting empty conditions dict"""
        # Arrange
        conditions = {}

        # Act
        hashable = _conditions_to_hashable(conditions)

        # Assert
        assert hashable == ()
        assert isinstance(hashable, tuple)

    def test_order_consistency(self):
        """Test that the same conditions always produce the same hashable tuple"""
        # Arrange
        conditions1 = {"b": 2, "a": 1, "c": 3}
        conditions2 = {"c": 3, "a": 1, "b": 2}

        # Act
        hashable1 = _conditions_to_hashable(conditions1)
        hashable2 = _conditions_to_hashable(conditions2)

        # Assert
        assert hashable1 == hashable2
        assert hashable1 == (("a", 1), ("b", 2), ("c", 3))

    def test_hashable_can_be_used_as_dict_key(self):
        """Test that the returned tuple can be used as a dictionary key"""
        # Arrange
        conditions = {"s1": 10.0, "ph": 7.4}
        hashable = _conditions_to_hashable(conditions)

        # Act & Assert
        test_dict = {hashable: "group_1"}
        assert test_dict[hashable] == "group_1"


class TestGroupMeasurements:
    """Test suite for group_measurements function"""

    def test_with_identical_conditions(self):
        """Test grouping measurements with identical conditions"""
        # Arrange
        species_data1 = [Mock(species_id="s1", prepared=10.0, initial=None)]
        species_data2 = [Mock(species_id="s1", prepared=10.0, initial=None)]

        measurement1 = Mock(
            species_data=species_data1, ph=7.4, temperature=25.0, group_id=None
        )
        measurement2 = Mock(
            species_data=species_data2, ph=7.4, temperature=25.0, group_id=None
        )

        enzmldoc = Mock(measurements=[measurement1, measurement2])

        # Act
        result = group_measurements(enzmldoc)

        # Assert
        assert result == enzmldoc
        assert measurement1.group_id == measurement2.group_id
        assert measurement1.group_id == "group_0"

    def test_with_different_conditions(self):
        """Test grouping measurements with different conditions"""
        # Arrange
        species_data1 = [Mock(species_id="s1", prepared=10.0, initial=None)]
        species_data2 = [
            Mock(species_id="s1", prepared=15.0, initial=None)
        ]  # Different concentration

        measurement1 = Mock(
            species_data=species_data1, ph=7.4, temperature=25.0, group_id=None
        )
        measurement2 = Mock(
            species_data=species_data2, ph=7.4, temperature=25.0, group_id=None
        )

        enzmldoc = Mock(measurements=[measurement1, measurement2])

        # Act
        result = group_measurements(enzmldoc)

        # Assert
        assert result == enzmldoc
        assert measurement1.group_id != measurement2.group_id
        assert measurement1.group_id == "group_0"
        assert measurement2.group_id == "group_1"

    def test_with_different_ph(self):
        """Test grouping measurements with different pH values"""
        # Arrange
        species_data1 = [Mock(species_id="s1", prepared=10.0, initial=None)]
        species_data2 = [Mock(species_id="s1", prepared=10.0, initial=None)]

        measurement1 = Mock(
            species_data=species_data1, ph=7.4, temperature=25.0, group_id=None
        )
        measurement2 = Mock(
            species_data=species_data2,
            ph=8.0,  # Different pH
            temperature=25.0,
            group_id=None,
        )

        enzmldoc = Mock(measurements=[measurement1, measurement2])

        # Act
        group_measurements(enzmldoc)

        # Assert
        assert measurement1.group_id != measurement2.group_id
        assert measurement1.group_id == "group_0"
        assert measurement2.group_id == "group_1"

    def test_with_no_measurements(self):
        """Test with document containing no measurements"""
        # Arrange
        enzmldoc = Mock(measurements=[])

        # Act
        result = group_measurements(enzmldoc)

        # Assert
        assert result == enzmldoc

    def test_with_single_measurement(self):
        """Test with document containing single measurement"""
        # Arrange
        species_data = [Mock(species_id="s1", prepared=10.0, initial=None)]
        measurement = Mock(
            species_data=species_data, ph=7.4, temperature=25.0, group_id=None
        )
        enzmldoc = Mock(measurements=[measurement])

        # Act
        result = group_measurements(enzmldoc)

        # Assert
        assert result == enzmldoc
        assert measurement.group_id == "group_0"

    def test_with_multiple_identical_and_different_conditions(self):
        """Test complex scenario with multiple measurements having various conditions"""
        # Arrange
        # Two measurements with identical conditions
        species_data1 = [Mock(species_id="s1", prepared=10.0, initial=None)]
        species_data2 = [Mock(species_id="s1", prepared=10.0, initial=None)]

        # One measurement with different conditions
        species_data3 = [Mock(species_id="s1", prepared=15.0, initial=None)]

        # Another measurement identical to the first two
        species_data4 = [Mock(species_id="s1", prepared=10.0, initial=None)]

        measurement1 = Mock(
            species_data=species_data1, ph=7.4, temperature=25.0, group_id=None
        )
        measurement2 = Mock(
            species_data=species_data2, ph=7.4, temperature=25.0, group_id=None
        )
        measurement3 = Mock(
            species_data=species_data3, ph=7.4, temperature=25.0, group_id=None
        )
        measurement4 = Mock(
            species_data=species_data4, ph=7.4, temperature=25.0, group_id=None
        )

        enzmldoc = Mock(
            measurements=[measurement1, measurement2, measurement3, measurement4]
        )

        # Act
        group_measurements(enzmldoc)

        # Assert
        # measurement1, measurement2, and measurement4 should have the same group_id
        assert measurement1.group_id == measurement2.group_id == measurement4.group_id
        assert measurement3.group_id != measurement1.group_id
        assert measurement1.group_id == "group_0"
        assert measurement3.group_id == "group_1"

    def test_group_id_format(self):
        """Test that group IDs follow the expected format"""
        # Arrange
        species_data1 = [Mock(species_id="s1", prepared=10.0, initial=None)]
        species_data2 = [Mock(species_id="s1", prepared=15.0, initial=None)]
        species_data3 = [Mock(species_id="s1", prepared=20.0, initial=None)]
        species_data4 = [Mock(species_id="s1", prepared=20.0, initial=None)]

        measurement1 = Mock(
            species_data=species_data1, ph=7.4, temperature=25.0, group_id=None
        )
        measurement2 = Mock(
            species_data=species_data2, ph=7.4, temperature=25.0, group_id=None
        )
        measurement3 = Mock(
            species_data=species_data3, ph=7.4, temperature=25.0, group_id=None
        )
        measurement4 = Mock(
            species_data=species_data4, ph=7.4, temperature=25.0, group_id=None
        )

        enzmldoc = Mock(
            measurements=[measurement1, measurement2, measurement3, measurement4]
        )

        # Act
        group_measurements(enzmldoc)

        # Assert
        assert measurement1.group_id == "group_0"
        assert measurement2.group_id == "group_1"
        assert measurement3.group_id == "group_2"
        assert measurement4.group_id == "group_2"


class TestGroupMeasurementsIntegration:
    """Integration tests using the existing fixtures"""

    def test_with_valid_measurement_fixture(self, measurement_valid):
        """Test group_measurements with the existing valid measurement fixture"""
        # Arrange
        original_measurements = measurement_valid.measurements.copy()

        # Act
        result = group_measurements(measurement_valid)

        # Assert
        assert result == measurement_valid
        assert len(measurement_valid.measurements) == len(original_measurements)

        # Check that all measurements got group_ids assigned
        for measurement in measurement_valid.measurements:
            assert measurement.group_id is not None
            assert measurement.group_id.startswith("group_")
