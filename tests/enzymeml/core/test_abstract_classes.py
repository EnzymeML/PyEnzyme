from pyenzyme.enzymeml.core.abstract_classes import AbstractSpecies
from pyenzyme.enzymeml.core.ontology import SBOTerm


class TestAbstractSpecies:

    def test_content(self):
        # Test consistency of inputs
        abstract = AbstractSpecies(
            name="SomeSpecies", vessel_id="v0",
            init_conc=10.0, unit="mmole / l", constant=True, meta_id="undefined",
            id="c0", boundary=True, ontology=SBOTerm.MACROMOLECULAR_COMPLEX, uri="URI", creator_id="a0"
        )

        assert abstract.name == "SomeSpecies"
        assert abstract.vessel_id == "v0"
        assert abstract.init_conc == 10.0
        assert abstract.unit == "mmole / l"
        assert abstract.constant is True
        assert abstract.meta_id == "METAID_C0"
        assert abstract.id == "c0"
        assert abstract.boundary is True
        assert abstract.ontology == SBOTerm.MACROMOLECULAR_COMPLEX
        assert abstract.uri == "URI"
        assert abstract.creator_id == "a0"

    def test_defaults(self):
        # Test if the defaults are the same
        abstract = AbstractSpecies(
            name="SomeSpecies", vessel_id="v0", constant=True, boundary=True, ontology=SBOTerm.MACROMOLECULAR_COMPLEX
        )

        assert not abstract.init_conc
        assert not abstract.unit
        assert abstract.constant is True
        assert not abstract.meta_id
        assert not abstract.id
        assert abstract.boundary is True
        assert abstract.ontology == SBOTerm.MACROMOLECULAR_COMPLEX
        assert not abstract.uri
