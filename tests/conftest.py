import pytest
import json
import yaml

from pyenzyme.enzymeml.core.enzymemldocument import EnzymeMLDocument
from pyenzyme.enzymeml.core.measurement import Measurement
from pyenzyme.enzymeml.core.measurementData import MeasurementData
from pyenzyme.enzymeml.core.replicate import Replicate
from pyenzyme.enzymeml.core.enzymereaction import EnzymeReaction
from pyenzyme.enzymeml.tools.unitcreator import UnitCreator
from pyenzyme.enzymeml.models.kineticmodel import KineticModel, KineticParameter


@pytest.fixture
def enzmldoc():
    return EnzymeMLDocument.fromJSON(
        open("./tests/fixtures/enzmldoc_object.json").read()
    )


@pytest.fixture
def reaction():
    return EnzymeReaction.fromJSON(open("./tests/fixtures/reaction_object.json").read())


@pytest.fixture
def measurement():
    return Measurement.fromJSON(open("./tests/fixtures/measurement_object.json").read())


@pytest.fixture
def measurement_data():
    return MeasurementData.fromJSON(
        open("./tests/fixtures/measurement_data_object.json").read()
    )


@pytest.fixture
def replicate():
    return Replicate.fromJSON(open("./tests/fixtures/replicate_object.json").read())


@pytest.fixture
def correct_model():
    parameters = [KineticParameter(name="x", value=10.0, unit="mmole / l")]
    return KineticModel(name="SomeModel", equation="s0 * x", parameters=parameters)


@pytest.fixture
def faulty_model():
    parameters = [KineticParameter(name="x", value=10.0, unit="mmole / l")]
    return KineticModel(name="SomeModel", equation="s10 * x", parameters=parameters)


@pytest.fixture
def always_pass():
    return yaml.safe_load(open("./tests/fixtures/validator_always_passes.yaml"))


@pytest.fixture
def should_fail():
    return yaml.safe_load(open("./tests/fixtures/validator_should_fail.yaml"))


@pytest.fixture
def template_example():
    return EnzymeMLDocument.fromJSON(open("tests/fixtures/template_result.json").read())


@pytest.fixture
def creator():
    return UnitCreator()


@pytest.fixture
def blank_enzmldoc():
    return EnzymeMLDocument(name="Test")
