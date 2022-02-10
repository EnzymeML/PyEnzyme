from pyenzyme.enzymeml.core.vessel import Vessel


class TestVessel:

    def test_content(self):
        """Tests consistency of content"""

        vessel = Vessel(
            name="SomeVessel", volume=100.0, unit="ml", constant=True,
            id="v0", meta_id="undefined", uri="URI", creator_id="a0"
        )

        assert vessel.name == "SomeVessel"
        assert vessel.volume == 100.0
        assert vessel.unit == "ml"
        assert vessel.constant is True
        assert vessel.id == "v0"
        assert vessel.meta_id == "METAID_V0"
        assert vessel.uri == "URI"
        assert vessel.creator_id == "a0"

    def test_defaults(self):
        """Tests default values"""

        vessel = Vessel(name="SomeVessel")

        assert vessel.name == "SomeVessel"
        assert vessel.constant is True
        assert not vessel.volume
        assert not vessel.unit
        assert not vessel.id
        assert not vessel.meta_id
        assert not vessel.uri
        assert not vessel.creator_id
        assert not vessel._unit_id
