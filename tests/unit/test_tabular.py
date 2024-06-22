import pytest
import pandas as pd
import pyenzyme as pe

from pyenzyme.units import mM, s
from pyenzyme.tabular import _measurement_to_pandas, to_pandas


class TestTabularExport:
    def test_single_measurement(self, measurement_valid):
        """Test that a single measurement can be converted to a pandas DataFrame"""

        # Act
        df = _measurement_to_pandas(measurement_valid.measurements[0])

        # Assert
        assert isinstance(df, pd.DataFrame), f"Expected a DataFrame. Got {type(df)}"

    def test_invalid_measurement(self, measurement_invalid):
        """Test that an invalid measurement raises a ValueError"""

        # Act
        with pytest.raises(ValueError):
            _measurement_to_pandas(measurement_invalid.measurements[0])

    def test_multiple_measurements(self, measurement_valid):
        """Test that multiple measurements can be converted to a pandas DataFrame"""

        # Act
        df = to_pandas(measurement_valid)

        # Assert
        total_time_len = sum(
            [len(m.species[0].time) for m in measurement_valid.measurements]
        )

        assert (
            df.shape[0] == total_time_len
        ), f"Expected {total_time_len} rows. Got {df.shape[0]}"
        assert df.shape[1] == 4, f"Expected 4 columns. Got {df.shape[1]}"
        assert isinstance(df, pd.DataFrame), f"Expected a DataFrame. Got {type(df)}"
        assert (
            df["id"].nunique() == 2
        ), f"Expected 2 unique IDs. Got {df['id'].nunique()}"

        for measurement in measurement_valid.measurements:
            df_sub = df[df["id"] == measurement.id]
            assert df_sub.shape[0] == len(
                measurement.species[0].time
            ), f"Expected {len(measurement.species[0].time)} rows. Got {df_sub.shape[0]}"

            for species in measurement.species:
                assert (
                    species.species_id in df.columns
                ), f"Expected column for {species}"


class TestTabularImport:
    def test_csv_import(self):
        """Test that a CSV file can be imported to a pandas DataFrame"""
        # Act
        meas = pe.read_csv("tests/fixtures/tabular/data.csv", data_unit=mM, time_unit=s)

        # Assert
        assert len(meas) == 2, f"Expected 2 measurements. Got {len(meas)}"

        for m in meas:
            assert len(m.species) == 2, f"Expected 2 species. Got {len(m.species)}"
            assert (
                len(m.species[0].time) == 11
            ), f"Expected 10 time points. Got {len(m.species[0].time)}"
            assert (
                len(m.species[1].time) == 11
            ), f"Expected 10 time points. Got {len(m.species[1].time)}"
            assert (
                m.species[0].data_unit == mM
            ), f"Expected mM. Got {m.species[0].data_unit}"
            assert (
                m.species[0].time_unit == s
            ), f"Expected s. Got {m.species[0].time_unit}"
            assert (
                m.species[1].data_unit == mM
            ), f"Expected mM. Got {m.species[1].data_unit}"
            assert (
                m.species[1].time_unit == s
            ), f"Expected s. Got {m.species[1].time_unit}"

    def test_excel_import(self):
        """Test that a Excel file can be imported to a pandas DataFrame"""
        # Act
        meas = pe.read_excel(
            "tests/fixtures/tabular/data.xlsx", data_unit=mM, time_unit=s
        )

        # Assert
        assert len(meas) == 2, f"Expected 2 measurements. Got {len(meas)}"

        for m in meas:
            assert len(m.species) == 2, f"Expected 2 species. Got {len(m.species)}"
            assert (
                len(m.species[0].time) == 11
            ), f"Expected 10 time points. Got {len(m.species[0].time)}"
            assert (
                len(m.species[1].time) == 11
            ), f"Expected 10 time points. Got {len(m.species[1].time)}"
            assert (
                m.species[0].data_unit == mM
            ), f"Expected mM. Got {m.species[0].data_unit}"
            assert (
                m.species[0].time_unit == s
            ), f"Expected s. Got {m.species[0].time_unit}"
            assert (
                m.species[1].data_unit == mM
            ), f"Expected mM. Got {m.species[1].data_unit}"
            assert (
                m.species[1].time_unit == s
            ), f"Expected s. Got {m.species[1].time_unit}"

    def test_invalid_types(self):
        """Test that an invalid CSV raises a ValueError"""
        # Act
        with pytest.raises(AssertionError):
            pe.read_csv(
                "tests/fixtures/tabular/data_invalid_chars.csv",
                data_unit=mM,
                time_unit=s,
            )

    def test_invalid_csv(self):
        """Test that an invalid CSV raises a ValueError"""
        # Act
        with pytest.raises(AssertionError):
            pe.read_csv(
                "tests/fixtures/tabular/data_invalid.csv",
                data_unit=mM,
                time_unit=s,
            )

    def test_invalid_excel(self):
        """Test that an invalid Excel raises a ValueError"""
        # Act
        with pytest.raises(AssertionError):
            pe.read_excel(
                "tests/fixtures/tabular/data_invalid.xlsx",
                data_unit=mM,
                time_unit=s,
            )
