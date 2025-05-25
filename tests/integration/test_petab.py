import re
import tempfile
import pytest

import pyenzyme as pe
from pyenzyme.petab.conditions import ConditionRow
from pyenzyme.petab.measurements import MeasurementRow
from pyenzyme.petab.observables import ObservableRow
from pyenzyme.petab.parameters import ParameterRow, PriorType


class TestPEtab:
    def test_to_petab(self):
        # Arrange
        doc = pe.read_enzymeml("tests/fixtures/petab/enzmldoc_reaction.json")

        # Act
        with tempfile.TemporaryDirectory() as tmp_dir:
            meta = pe.to_petab(doc, tmp_dir)
            problem = meta.problems[0]
            sbml_path = problem.sbml_files[0]
            condition_path = problem.condition_files[0]
            observable_path = problem.observable_files[0]
            measurement_path = problem.measurement_files[0]

            if isinstance(meta.parameter_file, list):
                raise ValueError(
                    "Parameter file is a list, but should be a single file"
                )
            else:
                parameter_path = meta.parameter_file

            # Assert
            expected_sbml = self._remove_uuid(
                open("tests/fixtures/petab/abts_measurement_model.xml").read()
            )
            expected_condition = open(
                "tests/fixtures/petab/abts_measurement_conditions.tsv"
            ).read()
            expected_observable = open(
                "tests/fixtures/petab/abts_measurement_observables.tsv"
            ).read()
            expected_measurement = open(
                "tests/fixtures/petab/abts_measurement_measurements.tsv"
            ).read()
            expected_parameter = open(
                "tests/fixtures/petab/abts_measurement_parameters.tsv"
            ).read()

            assert expected_sbml == self._remove_uuid(sbml_path.read_text())
            assert expected_condition == condition_path.read_text()
            assert expected_observable == observable_path.read_text()
            assert expected_measurement == measurement_path.read_text()
            assert expected_parameter == parameter_path.read_text()

    def _remove_uuid(self, s: str) -> str:
        return re.sub(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            "",
            s,
        )


class TestConditionRow:
    def test_from_measurement(self):
        # Arrange
        measurement = pe.Measurement(
            id="condition_1",
            name="condition_1",
        )

        measurement.add_to_species_data(
            species_id="species_1",
            initial=1.0,
        )

        measurement.add_to_species_data(
            species_id="species_2",
            initial=2.0,
        )

        measurement.add_to_species_data(
            species_id="species_3",
            initial=None,
        )

        # Act
        condition = ConditionRow.from_measurement(measurement)

        # Assert
        assert condition.condition_id == "condition_1"
        assert condition.condition_name == "condition_1"
        assert condition.species["species_1"] == 1.0
        assert condition.species["species_2"] == 2.0
        assert "species_3" not in condition.species

    def test_to_row(self):
        # Arrange
        condition = ConditionRow(
            conditionId="condition_1",
            conditionName="condition_1",
            species={
                "species_1": 1.0,
                "species_2": 2.0,
            },
        )

        # Act
        row = condition.to_row()

        # Assert
        assert row["conditionId"] == "condition_1"
        assert row["conditionName"] == "condition_1"
        assert row["species_1"] == 1.0
        assert row["species_2"] == 2.0


class TestMeasurementRow:
    def test_from_measurement(self):
        # Arrange
        measurement = pe.Measurement(
            id="measurement_1",
            name="measurement_1",
        )

        measurement.add_to_species_data(
            species_id="species_1",
            initial=1.0,
            data=[1.0, 2.0, 3.0],
            time=[0.0, 1.0, 2.0],
        )

        # Act
        meas_rows = MeasurementRow.from_measurement(measurement)

        # Assert
        assert len(meas_rows) == 3

        expected_data = [
            (0.0, 1.0),
            (1.0, 2.0),
            (2.0, 3.0),
        ]

        for meas_row, (t, x) in zip(meas_rows, expected_data):
            assert meas_row.observable_id == "species_1"
            assert meas_row.condition_id == "measurement_1"
            assert meas_row.measurement == x
            assert meas_row.time == t


class TestObservableRow:
    def test_from_enzymeml(self):
        # Arrange
        enzmldoc = pe.EnzymeMLDocument(name="test")

        # Add species
        meas = enzmldoc.add_to_measurements(
            id="measurement_1",
            name="measurement_1",
        )

        meas.add_to_species_data(
            species_id="species_1",
            initial=1.0,
            data=[1.0, 2.0, 3.0],
            time=[0.0, 1.0, 2.0],
        )

        meas.add_to_species_data(
            species_id="species_2",
            initial=2.0,
            data=[1.0, 2.0, 3.0],
            time=[0.0, 1.0, 2.0],
        )

        # Not observable
        meas.add_to_species_data(
            species_id="species_3",
            initial=3.0,
        )

        # Act
        obs_rows = ObservableRow.from_enzymeml(enzmldoc)
        obs_rows.sort(key=lambda x: x.observable_id)

        # Assert
        assert len(obs_rows) == 2
        assert obs_rows[0].observable_id == "species_1"
        assert obs_rows[1].observable_id == "species_2"

    def test_from_enzymeml_missing_observable(self):
        # Arrange
        enzmldoc = pe.EnzymeMLDocument(name="test")

        # Add species
        meas1 = enzmldoc.add_to_measurements(
            id="measurement_1",
            name="measurement_1",
        )

        meas1.add_to_species_data(
            species_id="species_1",
            initial=1.0,
            data=[1.0, 2.0, 3.0],
            time=[0.0, 1.0, 2.0],
        )

        meas1.add_to_species_data(
            species_id="species_2",
            initial=2.0,
            data=[1.0, 2.0, 3.0],
            time=[0.0, 1.0, 2.0],
        )

        # Create a second measurement with a different species
        meas2 = enzmldoc.add_to_measurements(
            id="measurement_2",
            name="measurement_2",
        )

        meas2.add_to_species_data(
            species_id="species_1",
            initial=1.0,
            data=[1.0, 2.0, 3.0],
            time=[0.0, 1.0, 2.0],
        )

        meas2.add_to_species_data(
            species_id="species_3",
            initial=3.0,
            data=[1.0, 2.0, 3.0],
            time=[0.0, 1.0, 2.0],
        )

        # Act
        with pytest.raises(ValueError):
            ObservableRow.from_enzymeml(enzmldoc)


class TestParameterRow:
    def test_from_parameter_missing_bounds(self):
        # Arrange
        parameter = pe.Parameter(
            id="parameter_1",
            symbol="parameter_1",
            name="parameter_1",
            value=1.0,
        )

        # Act
        with pytest.raises(ValueError):
            ParameterRow.from_parameter(parameter)

    def test_from_parameter(self):
        # Arrange
        parameter = pe.Parameter(
            id="parameter_1",
            symbol="parameter_1",
            name="parameter_1",
            value=1.0,
            lower_bound=0.0,
            upper_bound=1.0,
        )

        # Act
        parameter_row = ParameterRow.from_parameter(parameter)

        # Assert
        assert parameter_row.parameter_id == "parameter_1"
        assert parameter_row.parameter_name == "parameter_1"
        assert parameter_row.parameter_scale == "lin"
        assert parameter_row.lower_bound == 0.0
        assert parameter_row.upper_bound == 1.0
        assert parameter_row.nominal_value == 1.0
        assert parameter_row.estimate is True
        assert (
            parameter_row.initialization_prior_type == PriorType.PARAMETER_SCALE_UNIFORM
        )
        assert parameter_row.initialization_prior_parameters == []
        assert parameter_row.objective_prior_type == PriorType.PARAMETER_SCALE_UNIFORM
        assert parameter_row.objective_prior_parameters == []
