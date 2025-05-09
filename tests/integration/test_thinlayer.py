import pytest
import pyenzyme as pe
from pyenzyme.thinlayers.base import BaseThinLayer


class TestThinLayer:
    def test_base_thinlayer(self):
        # Arrange
        doc = pe.read_enzymeml("tests/fixtures/modeling/enzmldoc.json")

        # Act
        thinlayer = BaseThinLayer(enzmldoc=doc)

        # Assert
        expected_sbml, _ = pe.to_sbml(doc)
        expected_data = pe.to_pandas(doc, per_measurement=True)

        assert thinlayer.enzmldoc == doc
        assert thinlayer.sbml_xml == expected_sbml
        assert len(thinlayer.data) == len(expected_data)

    def test_base_thinlayer_with_measurement_ids(self):
        # Arrange
        doc = pe.read_enzymeml("tests/fixtures/modeling/enzmldoc.json")

        # Act
        thinlayer = BaseThinLayer(enzmldoc=doc, measurement_ids=["measurement0"])

        # Assert
        expected_sbml, _ = pe.to_sbml(doc)

        assert thinlayer.enzmldoc == doc
        assert thinlayer.sbml_xml == expected_sbml
        assert len(thinlayer.data) == 1

    def test_base_thinlayer_with_measurement_ids_not_in_doc(self):
        # Arrange
        doc = pe.read_enzymeml("tests/fixtures/modeling/enzmldoc.json")

        # Act
        with pytest.raises(ValueError):
            base = BaseThinLayer(enzmldoc=doc, measurement_ids=["measnotexisting"])
            base.data
