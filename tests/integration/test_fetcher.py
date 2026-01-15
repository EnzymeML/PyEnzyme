import httpx
import pytest

from pyenzyme.fetcher.chebi import fetch_chebi
from pyenzyme.fetcher.pdb import fetch_pdb
from pyenzyme.fetcher.pubchem import fetch_pubchem
from pyenzyme.fetcher.rhea import fetch_rhea
from pyenzyme.fetcher.uniprot import fetch_uniprot


class TestFetcher:
    @pytest.mark.remote
    def test_fetch_chebi_to_small_molecule(self):
        small_molecule = fetch_chebi("CHEBI:15377")
        assert small_molecule is not None
        assert small_molecule.id == "water"
        assert small_molecule.name == "water"
        assert small_molecule.canonical_smiles == "[H]O[H]"
        assert small_molecule.inchi == "InChI=1S/H2O/h1H2"
        assert small_molecule.inchikey == "XLYOFNOQVPJJNP-UHFFFAOYSA-N"
        assert small_molecule.ld_id == "OBO:CHEBI_15377"
        assert len(small_molecule.references) == 1
        assert (
            small_molecule.references[0]
            == "https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:15377"
        )

    @pytest.mark.remote
    def test_fetch_chebi_to_small_molecule_with_id(self):
        small_molecule = fetch_chebi("CHEBI:15377", smallmol_id="s1")
        assert small_molecule is not None
        assert small_molecule.id == "s1"
        assert small_molecule.name == "water"
        assert small_molecule.canonical_smiles == "[H]O[H]"
        assert small_molecule.inchi == "InChI=1S/H2O/h1H2"
        assert small_molecule.inchikey == "XLYOFNOQVPJJNP-UHFFFAOYSA-N"
        assert small_molecule.ld_id == "OBO:CHEBI_15377"
        assert len(small_molecule.references) == 1
        assert (
            small_molecule.references[0]
            == "https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:15377"
        )

    @pytest.mark.remote
    def test_fetch_chebi_to_small_molecule_invalid_id(self):
        with pytest.raises(ValueError):
            fetch_chebi("INVALID_ID")

    @pytest.mark.remote
    def test_fetch_uniprot_to_protein(self):
        protein = fetch_uniprot("P07327")
        assert protein is not None

        assert protein.id == "alcohol_dehydrogenase_1a"
        assert protein.name == "Alcohol dehydrogenase 1A"
        assert protein.constant is True
        assert protein.ecnumber == "1.1.1.1"
        assert protein.organism == "Homo sapiens"
        assert protein.organism_tax_id == "9606"

        assert protein.ld_id == "uniprot:P07327"
        assert "uniprot:P07327" in protein.ld_type
        assert len(protein.references) == 1
        assert protein.references[0] == "https://www.uniprot.org/uniprotkb/P07327"

    @pytest.mark.remote
    def test_fetch_uniprot_to_protein_with_prefix(self):
        protein = fetch_uniprot("uniprot:P07327")
        assert protein is not None

        assert protein.id == "alcohol_dehydrogenase_1a"
        assert protein.name == "Alcohol dehydrogenase 1A"
        assert protein.constant is True
        assert protein.ecnumber == "1.1.1.1"
        assert protein.organism == "Homo sapiens"
        assert protein.organism_tax_id == "9606"

        assert protein.ld_id == "uniprot:P07327"
        assert "uniprot:P07327" in protein.ld_type
        assert len(protein.references) == 1
        assert protein.references[0] == "https://www.uniprot.org/uniprotkb/P07327"

    @pytest.mark.remote
    def test_fetch_uniprot_to_protein_with_id(self):
        protein = fetch_uniprot("P07327", protein_id="p1")
        assert protein is not None

        assert protein.id == "p1"
        assert protein.name == "Alcohol dehydrogenase 1A"
        assert protein.constant is True
        assert protein.ecnumber == "1.1.1.1"
        assert protein.organism == "Homo sapiens"
        assert protein.organism_tax_id == "9606"

        assert protein.ld_id == "uniprot:P07327"
        assert "uniprot:P07327" in protein.ld_type
        assert len(protein.references) == 1
        assert protein.references[0] == "https://www.uniprot.org/uniprotkb/P07327"

    @pytest.mark.remote
    def test_fetch_rhea_to_reaction(self):
        reaction, small_molecules = fetch_rhea("RHEA:22864")

        reaction.reactants.sort(key=lambda x: x.species_id)
        reaction.products.sort(key=lambda x: x.species_id)
        small_molecules.sort(key=lambda x: x.id)

        assert reaction is not None
        assert len(small_molecules) == 2

        assert small_molecules[0].id == "d_lysinium_1"
        assert small_molecules[1].id == "l_lysinium_1"

        assert reaction.id == "RHEA:22864"
        assert reaction.name == "RHEA:22864"
        assert reaction.reversible is True

        assert len(reaction.reactants) == 1
        assert reaction.reactants[0].stoichiometry == 1
        assert reaction.reactants[0].species_id == small_molecules[1].id

        assert len(reaction.products) == 1
        assert reaction.products[0].stoichiometry == 1
        assert reaction.products[0].species_id == small_molecules[0].id

    @pytest.mark.remote
    def test_fetch_rhea_to_reaction_invalid_id(self):
        with pytest.raises(ValueError):
            fetch_rhea("INVALID_ID")

    @pytest.mark.remote
    def test_fetch_pubchem_to_small_molecule(self):
        small_molecule = fetch_pubchem(cid="2244")
        assert small_molecule is not None
        assert small_molecule.id == "2_acetyloxybenzoic_acid"
        assert small_molecule.name == "2-acetyloxybenzoic acid"
        assert small_molecule.canonical_smiles == "CC(=O)OC1=CC=CC=C1C(=O)O"
        assert small_molecule.inchikey == "BSYNRYMUTXBXSQ-UHFFFAOYSA-N"
        assert (
            small_molecule.inchi
            == "InChI=1S/C9H8O4/c1-6(10)13-8-5-3-2-4-7(8)9(11)12/h2-5H,1H3,(H,11,12)"
        )

    @pytest.mark.remote
    def test_fetch_pubchem_to_small_molecule_with_prefix(self):
        small_molecule = fetch_pubchem(cid="pubchem:2244")
        assert small_molecule is not None
        assert small_molecule.id == "2_acetyloxybenzoic_acid"
        assert small_molecule.name == "2-acetyloxybenzoic acid"
        assert small_molecule.canonical_smiles == "CC(=O)OC1=CC=CC=C1C(=O)O"
        assert small_molecule.inchikey == "BSYNRYMUTXBXSQ-UHFFFAOYSA-N"
        assert (
            small_molecule.inchi
            == "InChI=1S/C9H8O4/c1-6(10)13-8-5-3-2-4-7(8)9(11)12/h2-5H,1H3,(H,11,12)"
        )

    @pytest.mark.remote
    def test_fetch_pubchem_to_small_molecule_invalid_id(self):
        with pytest.raises(httpx.HTTPStatusError):
            fetch_pubchem(cid="162176127617627")

    @pytest.mark.remote
    def test_fetch_pdb_to_protein(self):
        protein = fetch_pdb("1a23")
        assert protein is not None
        assert protein.id == "1a23_1"
        assert (
            protein.name
            == "SOLUTION NMR STRUCTURE OF REDUCED DSBA FROM ESCHERICHIA COLI, MINIMIZED AVERAGE STRUCTURE"
        )
        assert (
            protein.sequence
            == "AQYEDGKQYTTLEKPVAGAPQVLEFFSFFCPHCYQFEEVLHISDNVKKKLPEGVKMTKYHVNFMGGDLGKDLTQAWAVAMALGVEDKVTVPLFEGVQKTQTIRSASDIRDVFINAGIKGEEYDAAWNSFVVKSLVAQQEKAAADVQLRGVPAMFVNGKYQLNPQGMDTSNMDVFVQQYADTVKYLSEKK"
        )

    @pytest.mark.remote
    def test_fetch_pdb_to_protein_with_prefix(self):
        protein = fetch_pdb("pdb:1a23")
        assert protein is not None
        assert protein.id == "1a23_1"
        assert (
            protein.name
            == "SOLUTION NMR STRUCTURE OF REDUCED DSBA FROM ESCHERICHIA COLI, MINIMIZED AVERAGE STRUCTURE"
        )
        assert (
            protein.sequence
            == "AQYEDGKQYTTLEKPVAGAPQVLEFFSFFCPHCYQFEEVLHISDNVKKKLPEGVKMTKYHVNFMGGDLGKDLTQAWAVAMALGVEDKVTVPLFEGVQKTQTIRSASDIRDVFINAGIKGEEYDAAWNSFVVKSLVAQQEKAAADVQLRGVPAMFVNGKYQLNPQGMDTSNMDVFVQQYADTVKYLSEKK"
        )

    @pytest.mark.remote
    def test_fetch_pdb_to_protein_invalid_id(self):
        with pytest.raises(ValueError):
            fetch_pdb("INVALID_ID")
