import tempfile
from pathlib import Path

from pydantic import BaseModel

import pyenzyme as pe
import pyenzyme.equations as peq
from pyenzyme.tools import to_dict_wo_json_ld


class TestSBML:
    def test_parse_sbml_odes(self):
        # Arrange
        path = Path("tests/fixtures/sbml/odes_example.omex")

        # Act
        enzmldoc = pe.from_sbml(path)

        # Assert
        parsed_doc = to_dict_wo_json_ld(enzmldoc)
        expected_doc = to_dict_wo_json_ld(
            pe.read_enzymeml("tests/fixtures/sbml/ode_example_enzml.json")
        )

        assert parsed_doc == expected_doc, (
            "Parsed document does not match expected document"
        )

    def test_v1_import(self):
        # Arrange
        path = Path("tests/fixtures/sbml/v1_example.omex")

        # Act
        enzmldoc = pe.from_sbml(path)

        # Assert
        parsed_doc = to_dict_wo_json_ld(enzmldoc)
        expected_doc = to_dict_wo_json_ld(
            pe.read_enzymeml("tests/fixtures/sbml/v1_example_enzml.json")
        )

        assert parsed_doc == expected_doc, (
            "Parsed document does not match expected document"
        )

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

        with tempfile.TemporaryDirectory() as dirname:
            path = Path(dirname) / "test.omex"
            pe.to_sbml(doc, path)

            # Act
            enzmldoc = pe.from_sbml(path)

            # Assert
            self.set_unit_name_as_id(enzmldoc)

            parsed_doc = to_dict_wo_json_ld(enzmldoc)
            expected_doc = to_dict_wo_json_ld(doc)

            # Remove spaces of equation
            for eq in parsed_doc["equations"]:
                eq["equation"] = eq["equation"].replace(" * ", "*")
                eq["equation"] = eq["equation"].replace(" / ", "/")

            assert parsed_doc == expected_doc, (
                "Parsed document does not match expected document"
            )

    def test_temperature_conversion(self):
        enzmldoc = pe.read_enzymeml("tests/fixtures/modeling/enzmldoc_reaction.json")
        enzmldoc.measurements = [enzmldoc.measurements[0]]
        enzmldoc.measurements[0].temperature = 0.0
        enzmldoc.measurements[0].temperature_unit = "°C"  # type: ignore

        with tempfile.TemporaryDirectory() as dirname:
            # Write to OMEX and read again
            path = Path(dirname) / "test.omex"
            pe.to_sbml(enzmldoc, path)
            enzmldoc = pe.from_sbml(path)

            assert enzmldoc.measurements[0].temperature == 273.15

            if enzmldoc.measurements[0].temperature_unit is not None:
                assert enzmldoc.measurements[0].temperature_unit.name == "Kelvin"
            else:
                raise ValueError("Temperature unit is None")

    def set_unit_name_as_id(self, obj):
        for key, value in obj:
            if isinstance(value, pe.UnitDefinition):
                value.id = value.name
            elif isinstance(value, BaseModel):
                self.set_unit_name_as_id(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, BaseModel):
                        self.set_unit_name_as_id(item)
