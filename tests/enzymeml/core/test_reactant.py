from pyenzyme.enzymeml.core.reactant import Reactant
from pyenzyme.enzymeml.core.ontology import SBOTerm


class TestReactant:

    def test_content(self):
        # Test consistency of inputs
        reactant = Reactant(
            name="SomeReactant", vessel_id="v0",
            init_conc=10.0, unit="mmole / l", constant=True, meta_id="undefined",
            id="s0", boundary=True, ontology=SBOTerm.MACROMOLECULAR_COMPLEX, uri="URI", creator_id="a0",
            inchi="AnInChICode", smiles="()(()-)", chebi_id="CHEBI:15377"
        )

        assert reactant.inchi == "AnInChICode"
        assert reactant.chebi_id == "CHEBI:15377"
        assert reactant.smiles == "()(()-)"

    def test_defaults(self):
        # Test if the defaults are the same
        reactant = Reactant(
            name="SomeReactant", vessel_id="v0"
        )

        assert reactant.constant is False
        assert reactant.boundary is False
        assert reactant.ontology == SBOTerm.SMALL_MOLECULE
        assert not reactant.inchi
        assert not reactant.smiles
        assert not reactant.chebi_id

    # def test_chebi_id_init(self):

    #     reactant = Reactant.fromChebiID(
    #         chebi_id="CHEBI:15377", vessel_id="v0", init_conc=10.0, unit="mmole / l"
    #     )

    #     assert reactant.chebi_id == "CHEBI:15377"
    #     assert reactant.name == "water"
    #     assert reactant.inchi == "InChI=1S/H2O/h1H2"
    #     assert reactant.smiles == "[H]O[H]"
    #     assert reactant.init_conc == 10.0
    #     assert reactant.unit == "mmole / l"
