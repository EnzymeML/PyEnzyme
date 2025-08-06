import os
import tempfile

import pyenzyme as pe
import pyenzyme.equations as peq
from pyenzyme.tools import to_dict_wo_json_ld


class TestEnzymeML:
    def test_end_to_end(self):
        # Arrange
        doc = pe.EnzymeMLDocument(name="Test")

        # Add Vessels
        vessel = doc.add_to_vessels(
            name="Vessel 1",
            volume=10.0,
            unit="ml",  # type: ignore
            id="v0",
        )

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
            vessel_id=vessel.id,
        )

        doc.equations += peq.build_equations(
            "s1'(t) = kcat * E_tot * s0(t) / (K_m + s0(t))",
            "E_tot = 100",
            unit_mapping={
                "kcat": "1 / s",
                "K_m": "mmol / l",
                "E_tot": "mmol / l",
            },
            enzmldoc=doc,
        )

        doc.measurements += pe.from_excel(
            "tests/fixtures/tabular/data.xlsx",
            data_unit="mmol / l",
            time_unit="s",
        )

        for parameter in doc.parameters:
            parameter.lower_bound = 0.0
            parameter.upper_bound = 100.0
            parameter.stderr = 0.1

        for meas in doc.measurements:
            meas.temperature = 298.15
            meas.temperature_unit = "K"  # type: ignore
            meas.ph = 7.0

        with tempfile.TemporaryDirectory() as tmpdir:
            enzmldoc_path = os.path.join(tmpdir, "enzymeml.omex")
            pe.write_enzymeml(doc, enzmldoc_path)

            # Load the saved EnzymeML document
            loaded_doc = pe.read_enzymeml(enzmldoc_path)

            # Assert
            assert to_dict_wo_json_ld(loaded_doc) == to_dict_wo_json_ld(doc)
