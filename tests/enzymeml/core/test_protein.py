from pyenzyme.enzymeml.core.protein import Protein
from pyenzyme.enzymeml.core.ontology import SBOTerm


class TestProtein:

    def test_content(self):
        # Test consistency of inputs
        protein = Protein(
            name="SomeProtein", vessel_id="v0",
            init_conc=10.0, unit="mmole / l", constant=True, meta_id="undefined",
            id="p0", boundary=True, ontology=SBOTerm.MACROMOLECULAR_COMPLEX, uri="URI", creator_id="a0",
            sequence="HGTHMLAP", ecnumber="1.1.1.1", organism="SomeOrganism", organism_tax_id="2894792", uniprotid="P0A955"
        )

        assert protein.sequence == "HGTHMLAP"
        assert protein.ecnumber == "1.1.1.1"
        assert protein.organism == "SomeOrganism"
        assert protein.organism_tax_id == "2894792"

    def test_defaults(self):
        # Test if the defaults are the same
        protein = Protein(
            name="SomeProtein", vessel_id="v0"
        )

        assert protein.constant is True
        assert protein.boundary is False
        assert protein.ontology == SBOTerm.PROTEIN
        assert not protein.sequence
        assert not protein.ecnumber
        assert not protein.organism
        assert not protein.organism_tax_id
        assert not protein.uniprotid

    def test_uniprot_id_init(self):

        protein = Protein.fromUniProtID(
            uniprotid="P0A955", vessel_id="v0", init_conc=10.0, unit="mmole / l"
        )

        assert protein.uniprotid == "P0A955"
        assert protein.name == "Phospho-2-keto-3-deoxygluconate aldolase"
        assert protein.sequence == "MKNWKTSAESILTTGPVVPVIVVKKLEHAVPMAKALVAGGVRVLEVTLRTECAVDAIRAIAKEVPEAIVGAGTVLNPQQLAEVTEAGAQFAISPGLTEPLLKAATEGTIPLIPGISTVSELMLGMDYGLKEFKFFPAEANGGVKALQAIAGPFSQVRFCPTGGISPANYRDYLALKSVLCIGGSWLVPADALEAGDYDRITKLAREAVEGAKL"
        assert protein.ecnumber == "4.1.2.14"
        assert protein.init_conc == 10.0
        assert protein.unit == "mmole / l"
        assert protein.vessel_id == "v0"
