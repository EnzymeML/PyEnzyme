import pytest
import requests

import pyenzyme.fetcher.uniprot as uniprot
from pyenzyme.fetcher.uniprot import fetch_uniprot

# Trimmed UniProt REST response for an unreviewed (TrEMBL) entry: no recommendedName
TREMBL_ENTRY = {
    "entryType": "UniProtKB unreviewed (TrEMBL)",
    "primaryAccession": "Q7DDU0",
    "uniProtkbId": "Q7DDU0_NEIMB",
    "annotationScore": 1.0,
    "organism": {
        "scientificName": "Neisseria meningitidis serogroup B (strain ATCC BAA-335 / MC58)",
        "taxonId": 122586,
    },
    "proteinDescription": {
        "submissionNames": [
            {
                "fullName": {"value": "Polysialic acid capsule biosynthesis protein SiaC"},
                "ecNumbers": [{"value": "2.5.1.56"}],
            }
        ]
    },
    "sequence": {"value": "MQNNNEF", "length": 7, "molWeight": 800},
}


class FakeResponse:
    def __init__(self, data=TREMBL_ENTRY, status_code=200):
        self.data = data
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(response=self)

    def json(self):
        return self.data


def test_fetch_uniprot_falls_back_to_submission_name(monkeypatch):
    monkeypatch.setattr(uniprot.requests, "get", lambda url: FakeResponse())

    protein = fetch_uniprot("Q7DDU0")

    assert protein.name == "Polysialic acid capsule biosynthesis protein SiaC"
    assert protein.id == "polysialic_acid_capsule_biosynthesis_protein_siac"
    assert protein.ecnumber == "2.5.1.56"
    assert protein.organism_tax_id == "122586"
    assert protein.ld_id == "uniprot:Q7DDU0"


def test_fetch_uniprot_unknown_id_is_value_error(monkeypatch):
    monkeypatch.setattr(
        uniprot.requests, "get", lambda url: FakeResponse(status_code=404)
    )

    with pytest.raises(ValueError, match="invalid or not found"):
        fetch_uniprot("P07327-2")


def test_fetch_uniprot_server_error_is_connection_error(monkeypatch):
    monkeypatch.setattr(
        uniprot.requests, "get", lambda url: FakeResponse(status_code=503)
    )

    with pytest.raises(ConnectionError):
        fetch_uniprot("P07327")


def test_fetch_uniprot_inactive_entry(monkeypatch):
    deleted = {
        "entryType": "Inactive",
        "primaryAccession": "A0A008APQ8",
        "inactiveReason": {
            "inactiveReasonType": "DELETED",
            "deletedReason": "Not part of a reference proteome",
        },
    }
    monkeypatch.setattr(uniprot.requests, "get", lambda url: FakeResponse(deleted))

    with pytest.raises(ValueError, match="inactive \\(DELETED: Not part of"):
        fetch_uniprot("A0A008APQ8")


def test_fetch_uniprot_strips_whitespace(monkeypatch):
    urls = []
    monkeypatch.setattr(
        uniprot.requests, "get", lambda url: urls.append(url) or FakeResponse()
    )

    fetch_uniprot(" Q7DDU0\n")

    assert urls == ["https://rest.uniprot.org/uniprotkb/Q7DDU0.json"]
