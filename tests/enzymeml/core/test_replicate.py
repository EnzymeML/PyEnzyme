import pytest

from pyenzyme.enzymeml.core.replicate import Replicate
from pyenzyme.enzymeml.core.ontology import DataTypes
from pyenzyme.enzymeml.core.exceptions import DataError


class TestReplicate:

    def test_content(self):
        """Tests consistency of content"""

        replicate = Replicate(
            id="repl_s0_1", species_id="s0", measurement_id="m0",
            data_type=DataTypes.CONCENTRATION, time_unit="min", time=[1, 2, 3],
            data_unit="mmole / l", data=[1, 1, 1], is_calculated=False, uri="URI", creator_id="a0"
        )

        assert replicate.id == "repl_s0_1"
        assert replicate.species_id == "s0"
        assert replicate.measurement_id == "m0"
        assert replicate.data_type == DataTypes.CONCENTRATION
        assert replicate.time_unit == "min"
        assert replicate.data_unit == "mmole / l"
        assert replicate.data == [1, 1, 1]
        assert replicate.time == [1, 2, 3]
        assert replicate.uri == "URI"
        assert replicate.creator_id == "a0"
        assert replicate.is_calculated is False

    def test_defaults(self):
        """Tests the default arguments"""

        replicate = Replicate(
            id="repl_s0_1", species_id="s0", data_unit="mmole", time_unit="min"
        )

        assert replicate.id == "repl_s0_1"
        assert replicate.species_id == "s0"
        assert replicate.data_type == DataTypes.CONCENTRATION
        assert replicate.is_calculated is False
        assert not replicate.measurement_id
        assert not replicate.data
        assert not replicate.time
        assert not replicate.uri
        assert not replicate.creator_id

    def test_data_completeness(self):
        """Tests if correct error messages are thrown at missing data"""

        with pytest.raises(DataError):
            Replicate(
                id="repl_s0_1", species_id="s0", measurement_id="m0",
                data_type=DataTypes.CONCENTRATION, time_unit="min",
                data_unit="mmole / l", data=[1, 1, 1], is_calculated=False, uri="URI", creator_id="a0"
            )

        with pytest.raises(DataError):
            Replicate(
                id="repl_s0_1", species_id="s0", measurement_id="m0",
                data_type=DataTypes.CONCENTRATION, time_unit="min",
                data_unit="mmole / l", data=[1, 1, 1], time=[1, 2], is_calculated=False, uri="URI", creator_id="a0"
            )
