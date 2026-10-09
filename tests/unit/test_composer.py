import pytest

import pyenzyme.composer as composer
from pyenzyme.composer import _fetch_with_fetchers, compose
from pyenzyme.versions import v2


def test_returns_first_successful_fetcher():
    def boom(_):
        raise ConnectionError("down")

    def ok(entity_id):
        return f"fetched:{entity_id}"

    assert _fetch_with_fetchers("X1", [boom, ok], "protein") == "fetched:X1"


def test_error_aggregates_every_fetcher_reason():
    def bad_request(_):
        raise ValueError("400 Bad Request")

    def not_found(_):
        raise KeyError("404")

    with pytest.raises(ValueError) as exc:
        _fetch_with_fetchers("X1", [bad_request, not_found], "protein")

    msg = str(exc.value)
    # names the entity, the type, and each fetcher's real failure reason
    assert "No protein fetcher succeeded for X1" in msg
    assert "bad_request: ValueError: 400 Bad Request" in msg
    assert "not_found: KeyError" in msg


def test_error_chains_last_fetcher_exception():
    def bad_request(_):
        raise ValueError("400 Bad Request")

    def not_found(_):
        raise KeyError("404")

    with pytest.raises(ValueError) as exc:
        _fetch_with_fetchers("X1", [bad_request, not_found], "protein")

    assert isinstance(exc.value.__cause__, KeyError)


def fake_rhea(_):
    mannac = v2.SmallMolecule(id="mannac", name="ManNAc", constant=False)
    mannac.ld_id = "OBO:CHEBI_63153"
    water = v2.SmallMolecule(id="water", name="Water", constant=False)
    water.ld_id = "OBO:CHEBI_15377"
    reaction = v2.Reaction(id="RHEA:19273", name="RHEA:19273", reversible=False)
    reaction.add_to_reactants(species_id="mannac", stoichiometry=1)
    reaction.add_to_reactants(species_id="water", stoichiometry=1)
    reaction.ld_id = "rhea:19273"
    return reaction, [mannac, water]


def compose_rhea(monkeypatch, id_mapping):
    monkeypatch.setattr(composer, "REACTION_FETCHERS", [fake_rhea])
    return compose(name="test", reactions=["RHEA:19273"], id_mapping=id_mapping)


def test_id_mapping_renames_reaction_species(monkeypatch):
    doc = compose_rhea(monkeypatch, {"CHEBI:63153": "ManNAc"})

    assert {sm.id for sm in doc.small_molecules} == {"ManNAc", "water"}
    (reaction,) = doc.reactions
    assert [r.species_id for r in reaction.reactants] == ["ManNAc", "water"]


@pytest.mark.parametrize("key", ["chebi:63153", "63153", "OBO:CHEBI_63153"])
def test_id_mapping_key_forms(monkeypatch, key):
    doc = compose_rhea(monkeypatch, {key: "ManNAc"})

    assert {sm.id for sm in doc.small_molecules} == {"ManNAc", "water"}


def test_id_mapping_does_not_match_partial_ids(monkeypatch):
    # CHEBI:1 is a prefix of CHEBI:15377 (water) but a different molecule
    doc = compose_rhea(monkeypatch, {"CHEBI:1": "X"})

    assert {sm.id for sm in doc.small_molecules} == {"mannac", "water"}


@pytest.mark.parametrize(
    "id_mapping",
    [
        {"CHEBI:63153": "S", "CHEBI:15377": "S"},  # two keys, same new ID
        {"CHEBI:63153": "water"},  # new ID taken by an unmapped species
    ],
)
def test_id_mapping_rejects_duplicate_ids(monkeypatch, id_mapping):
    with pytest.raises(ValueError, match="same ID"):
        compose_rhea(monkeypatch, id_mapping)
