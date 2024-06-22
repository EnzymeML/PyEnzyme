import pytest
import pyenzyme as pe


@pytest.fixture
def measurement_valid():
    return pe.EnzymeMLDocument.model_validate_json(
        open("tests/fixtures/tabular/measurement_valid.json").read()
    )


@pytest.fixture
def measurement_invalid():
    return pe.EnzymeMLDocument.model_validate_json(
        open("tests/fixtures/tabular/measurement_invalid.json").read()
    )
