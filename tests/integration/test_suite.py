import json
import pyenzyme as pe
from pyenzyme.suite import EnzymeMLSuite
from pytest_httpx import HTTPXMock

from pyenzyme.tools import to_dict_wo_json_ld
from pyenzyme.versions import v2


class TestSuite:
    def test_fetch_current(self, httpx_mock: HTTPXMock):
        # Arrange
        with open("tests/fixtures/sbml/ode_example_enzml.json", "r") as f:
            data = json.load(f)
            httpx_mock.add_response(json={"data": {"content": data}})

        # Act
        suite = EnzymeMLSuite("https://test_url")
        expected = v2.EnzymeMLDocument.model_validate(data)
        doc = suite.get_current()

        # Assert
        assert to_dict_wo_json_ld(doc) == to_dict_wo_json_ld(expected)

    def test_update_current(self, httpx_mock: HTTPXMock):
        # Arrange
        with open("tests/fixtures/sbml/ode_example_enzml.json", "r") as f:
            data = pe.read_enzymeml_from_string(json.load(f))
            httpx_mock.add_response(
                match_json=json.loads(data.model_dump_json()),
            )

        # Act
        suite = EnzymeMLSuite("https://test_url")
        suite.update_current(data)
