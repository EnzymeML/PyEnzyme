import tempfile
from pathlib import Path

import pyenzyme as pe
import pyenzyme.equations as peq
from pyenzyme import EnzymeMLDocument
from pyenzyme.tools import to_dict_wo_json_ld, get_all_parameters
from pyenzyme.units import mM, s, K, ml


class TestSBML:
    def test_parse_sbml_odes(self):
        # Arrange
        path = Path("tests/fixtures/sbml/odes_example.omex")

        # Act
        enzmldoc = EnzymeMLDocument.from_sbml(path)

        # Assert
        parsed_doc = to_dict_wo_json_ld(enzmldoc)
        expected_doc = to_dict_wo_json_ld(
            EnzymeMLDocument.read("tests/fixtures/sbml/ode_example_enzml.json")
        )

        assert (
            parsed_doc == expected_doc
        ), "Parsed document does not match expected document"

    def test_v1_import(self):
        # Arrange
        path = Path("tests/fixtures/sbml/v1_example.omex")

        # Act
        enzmldoc = EnzymeMLDocument.from_sbml(path)

        # Assert
        parsed_doc = to_dict_wo_json_ld(enzmldoc)
        expected_doc = to_dict_wo_json_ld(
            EnzymeMLDocument.read("tests/fixtures/sbml/v1_example_enzml.json")
        )

        assert (
            parsed_doc == expected_doc
        ), "Parsed document does not match expected document"

    def test_end_to_end(self):
        # Arrange

        doc = pe.EnzymeMLDocument(name="Test")

        ml.id = "u0"
        s.id = "u1"
        mM.id = "u2"
        K.id = "u3"

        # Add Vessels
        vessel = doc.add_to_vessels(name="Vessel 1", volume=10.0, unit=ml, id="v0")

        # Add Species
        substrate = doc.add_to_small_molecules(
            id="s0",
            name="Substrate",
            vessel_id=vessel.id,
            canonical_smiles="CC(=O)O",
            inchikey="QTBSBXVTEAMEQO-UHFFFAOYSA-N",
        )

        doc.add_to_small_molecules(
            id="s1",
            name="Product",
            vessel_id=vessel.id,
            canonical_smiles="CC(=O)O",
            inchikey="QTBSBXVTEAMEQO-UHFFFAOYSA-N",
        )

        # Add Enzyme
        enzyme = doc.add_to_proteins(
            id="p0",
            name="Enzyme",
            sequence="MTEY",
            vessel_id=vessel.id,
            ecnumber="1.1.1.1",
            organism="E.coli",
            organism_tax_id="12345",
        )

        doc.add_to_complexes(
            id="c0",
            name="Enzyme-Substrate Complex",
            participants=[enzyme.id, substrate.id],
        )

        doc.equations += peq.build_equations(
            "s1'(t) = kcat * E_tot * s0(t) / (K_m + s0(t))",
            "E_tot = 100",
            unit_mapping={"kcat": 1 / s, "K_m": mM, "E_tot": mM},
            enzmldoc=doc,
        )

        doc.measurements += pe.read_excel(
            "tests/fixtures/tabular/data.xlsx",
            data_unit=mM,
            time_unit=s,
        )

        for parameter in get_all_parameters(doc):
            parameter.lower = 0.0
            parameter.upper = 100.0
            parameter.stderr = 0.1

        for meas in doc.measurements:
            meas.temperature = 298.15
            meas.temperature_unit = K
            meas.ph = 7.0

        with tempfile.TemporaryDirectory() as dirname:
            path = Path(dirname) / "test.omex"
            doc.to_sbml(path)

            # Act
            enzmldoc = EnzymeMLDocument.from_sbml(path)

            # Assert
            parsed_doc = to_dict_wo_json_ld(enzmldoc)
            expected_doc = to_dict_wo_json_ld(doc)

            # Remove spaces of equation
            for eq in parsed_doc["equations"]:
                eq["equation"] = eq["equation"].replace(" * ", "*")
                eq["equation"] = eq["equation"].replace(" / ", "/")

            assert (
                parsed_doc == expected_doc
            ), "Parsed document does not match expected document"
