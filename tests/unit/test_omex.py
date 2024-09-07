from pathlib import Path

import pandas as pd
import pytest

from pyenzyme.sbml import read_sbml_omex


class TestOmex:
    def test_valid_omex(self):
        # Arrange
        path = Path("./tests/fixtures/omex/valid.omex")

        # Arrange
        sbml_file, data = read_sbml_omex(path=path)

        # Assert
        expected_data = pd.read_csv("./tests/fixtures/tabular/data.tsv", sep="\t")

        assert sbml_file is not None, "SBML file is None"
        assert data is not None, "Data is None"
        assert len(data) > 0, "Data is empty"
        assert isinstance(data, dict), "Data is not a dict"

        assert "./data.tsv" in data, "Key 'something' not found in data"
        assert data["./data.tsv"] is not None, "Data is None"
        assert data["./data.tsv"].equals(
            expected_data
        ), "Data is not equal to expected data"

    def test_invalid_omex_no_master(self):
        # Arrange
        path = Path("./tests/fixtures/omex/invalid_no_master.omex")

        # Act
        with pytest.raises(ValueError):
            sbml_file, data = read_sbml_omex(path=path)
