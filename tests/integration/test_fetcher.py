import pytest
from pyenzyme.fetcher.chebi import fetch_chebi_to_small_molecule
from pyenzyme.fetcher.rhea import fetch_rhea_to_reaction
from pyenzyme.fetcher.uniprot import fetch_uniprot_to_protein


class TestFetcher:
    def test_fetch_chebi_to_small_molecule(self):
        small_molecule = fetch_chebi_to_small_molecule("CHEBI:15377")
        assert small_molecule is not None
        assert small_molecule.id == "CHEBI_15377"
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

    def test_fetch_chebi_to_small_molecule_invalid_id(self):
        with pytest.raises(ValueError):
            fetch_chebi_to_small_molecule("INVALID_ID")

    def test_fetch_uniprot_to_protein(self):
        protein = fetch_uniprot_to_protein("P07327")
        assert protein is not None

        assert protein.id == "P07327"
        assert protein.name == "Alcohol dehydrogenase 1A"
        assert protein.constant is True
        assert protein.ecnumber == "1.1.1.1"
        assert protein.organism == "Homo sapiens"
        assert protein.organism_tax_id == "9606"

        assert protein.ld_id == "uniprot:P07327"
        assert "uniprot:P07327" in protein.ld_type
        assert len(protein.references) == 1
        assert protein.references[0] == "https://www.uniprot.org/uniprotkb/P07327"

    def test_fetch_rhea_to_reaction(self):
        reaction, small_molecules = fetch_rhea_to_reaction("RHEA:22864")

        reaction.species.sort(key=lambda x: x.species_id)
        small_molecules.sort(key=lambda x: x.id)

        assert reaction is not None
        assert len(small_molecules) == 2

        assert small_molecules[0].id == "CHEBI_32551"
        assert small_molecules[1].id == "CHEBI_32557"

        assert reaction.id == "RHEA:22864"
        assert reaction.name == "RHEA:22864"
        assert reaction.reversible is True

        assert len(reaction.species) == 2
        assert reaction.species[0].stoichiometry == 1
        assert reaction.species[0].species_id == small_molecules[0].id
        assert reaction.species[1].stoichiometry == -1
        assert reaction.species[1].species_id == small_molecules[1].id

    def test_fetch_rhea_to_reaction_invalid_id(self):
        with pytest.raises(ValueError):
            fetch_rhea_to_reaction("INVALID_ID")
