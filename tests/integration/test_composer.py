import pytest
import pyenzyme as pe
from pyenzyme.tools import to_dict_wo_json_ld


class TestComposer:
    def test_compose(self):
        # Act
        doc = pe.compose(
            name="test",
            vessel=pe.Vessel(
                id="vessel",
                name="vessel",
                volume=1.0,
                unit="ml",  # type: ignore
            ),
            proteins=["PDB:1a23"],
            small_molecules=["CHEBI:32551"],
            reactions=["RHEA:22864"],
        )

        # Assert
        expected_doc = pe.read_enzymeml("tests/fixtures/compose/expected_compose.json")
        assert to_dict_wo_json_ld(doc) == to_dict_wo_json_ld(expected_doc)

    def test_compose_with_prefix(self):
        # Act
        doc = pe.compose(
            name="test",
            vessel=pe.Vessel(
                id="vessel",
                name="vessel",
                volume=1.0,
                unit="ml",  # type: ignore
            ),
            proteins=["pdb:1a23"],
            small_molecules=["CHEBI:32551"],
            reactions=["RHEA:22864"],
        )

        # Assert
        expected_doc = pe.read_enzymeml("tests/fixtures/compose/expected_compose.json")
        assert to_dict_wo_json_ld(doc) == to_dict_wo_json_ld(expected_doc)

    def test_compose_no_vessel(self):
        # Act
        doc = pe.compose(
            name="test",
            proteins=["1A23"],
            small_molecules=["CHEBI:32551"],
            reactions=["RHEA:22864"],
        )

        # Assert
        expected_doc = pe.read_enzymeml(
            "tests/fixtures/compose/expected_compose_no_vessel.json"
        )
        assert to_dict_wo_json_ld(doc) == to_dict_wo_json_ld(expected_doc)

    def test_compose_invalid_id(self):
        # Act
        # Invalid Protein ID
        with pytest.raises(ValueError):
            pe.compose(
                name="test",
                proteins=["1A23", "INVALID"],
            )
        # Invalid Small Molecule ID
        with pytest.raises(ValueError):
            pe.compose(
                name="test",
                small_molecules=["CHEBI:32551", "INVALID"],
            )

        # Invalid Reaction ID
        with pytest.raises(ValueError):
            pe.compose(
                name="test",
                reactions=["RHEA:22864", "INVALID"],
            )
