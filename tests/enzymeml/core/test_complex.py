import pytest

from pyenzyme.enzymeml.core.complex import Complex
from pyenzyme.enzymeml.core.ontology import SBOTerm
from pyenzyme.enzymeml.core.exceptions import ParticipantIdentifierError


class TestComplex:

    def test_content(self):
        # Test consistency of inputs
        complex = Complex(
            name="SomeComplex", participants=["s0", "p0"], vessel_id="v0",
            init_conc=10.0, unit="mmole / l", constant=True, meta_id="undefined",
            id="c0", boundary=True, ontology=SBOTerm.MACROMOLECULAR_COMPLEX, uri="URI", creator_id="a0"
        )

        assert complex.participants == ["s0", "p0"]

    def test_defaults(self):
        # Test if the defaults are the same
        complex = Complex(
            name="SomeComplex", participants=["s0", "p0"], vessel_id="v0"
        )

        assert complex.constant is False
        assert complex.boundary is False
        assert complex.ontology == SBOTerm.MACROMOLECULAR_COMPLEX

    def test_validator_participants(self):
        # Negative test case to see if false IDs are recognized
        with pytest.raises(ParticipantIdentifierError) as exc_info:
            Complex(
                name="SomeComplex", participants=["x0", "1", "a", "&"], vessel_id="v0"
            )
