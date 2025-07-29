import pandas as pd

from mdmodels.units.converter import convert_unit
from pyenzyme.sbml.versions.v1 import (
    DataAnnot,
    ReactantAnnot,
    ComplexAnnot,
    ProteinAnnot,
)


class TestSBMLAnnotV1:
    def test_reactant_annotation(self):
        # Arrange
        xml_string = """
            <enzymeml:reactant xmlns:enzymeml="http://sbml.org/enzymeml/version2">
                <enzymeml:inchi>SomeInChI</enzymeml:inchi>
                <enzymeml:smiles>SomeSmiles</enzymeml:smiles>
                <enzymeml:chebiID>29111</enzymeml:chebiID>
            </enzymeml:reactant>
        """

        # Act
        obj = ReactantAnnot.from_xml(xml_string)

        # Assert
        assert obj.inchi == "SomeInChI", "InChI is different"
        assert obj.smiles == "SomeSmiles", "SMILES is different"
        assert obj.chebi_id == "29111", "Chebi ID is different"

    def test_complex_annotation(self):
        # Arrange
        xml_string = """
            <enzymeml:complex xmlns:enzymeml="http://sbml.org/enzymeml/version2">
                <enzymeml:participant>s0</enzymeml:participant>
                <enzymeml:participant>s1</enzymeml:participant>
            </enzymeml:complex>
        """

        # Act
        obj = ComplexAnnot.from_xml(xml_string)

        # Assert
        assert len(obj.participants) == 2, "Expected 2 participants"
        assert obj.participants[0] == "s0", "Expected participant 's0'"
        assert obj.participants[1] == "s1", "Expected participant 's1'"

    def test_protein_annotation(self):
        # Arrange
        xml_string = """
            <enzymeml:protein xmlns:enzymeml="http://sbml.org/enzymeml/version2">
                <enzymeml:sequence>HLV</enzymeml:sequence>
                <enzymeml:ECnumber>3.1.1.43</enzymeml:ECnumber>
                <enzymeml:uniprotID>B0RS62</enzymeml:uniprotID>
                <enzymeml:organism>SomeOrganism</enzymeml:organism>
                <enzymeml:organismTaxID>12345</enzymeml:organismTaxID>
            </enzymeml:protein>
        """

        # Act
        obj = ProteinAnnot.from_xml(xml_string)

        # Assert
        assert obj.uniprotid == "B0RS62", "UniProt ID is different"
        assert obj.sequence == "HLV", "Sequence is different"
        assert obj.ecnumber == "3.1.1.43", "EC number is different"
        assert obj.organism == "SomeOrganism", "Organism is different"
        assert obj.organism_tax_id == "12345", "Organism tax ID is different"

    def test_data_annotation(self):
        # Arrange
        xml_string = """
            <enzymeml:data xmlns:enzymeml="http://sbml.org/enzymeml/version2">
                <enzymeml:formats>
                    <enzymeml:format id="format0">
                        <enzymeml:column type="time" unit="u4" index="0"/>
                        <enzymeml:column replica="sub1_repl1" species="s0" type="conc" unit="u1" index="1"
                                         isCalculated="False"/>
                        <enzymeml:column replica="sub2_repl1" species="s1" type="conc" unit="u1" index="2"
                                         isCalculated="False"/>
                        <enzymeml:column replica="prod1_repl1" species="s2" type="conc" unit="u1" index="3"
                                         isCalculated="False"/>
                        <enzymeml:column replica="prod2_repl1" species="s3" type="conc" unit="u1" index="4"
                                         isCalculated="False"/>
                    </enzymeml:format>
                </enzymeml:formats>
                <enzymeml:listOfMeasurements>
                    <enzymeml:measurement file="file0" id="m0" name="Cephalexin synthesis 1">
                        <enzymeml:initConc protein="p0" value="0.0002" unit="u1"/>
                        <enzymeml:initConc reactant="s0" value="20.0" unit="u1"/>
                        <enzymeml:initConc reactant="s1" value="10.0" unit="u1"/>
                        <enzymeml:initConc reactant="s2" value="0.0" unit="u1"/>
                        <enzymeml:initConc reactant="s3" value="2.0" unit="u1"/>
                    </enzymeml:measurement>
                </enzymeml:listOfMeasurements>
                <enzymeml:files>
                    <enzymeml:file file="./data/m0.csv" format="format0" id="file0"/>
                </enzymeml:files>
            </enzymeml:data>
        """

        data = pd.read_csv(
            "./tests/fixtures/sbml/v1_meas.csv",
            header=None,
        )

        # Act
        obj = DataAnnot.from_xml(xml_string)
        measurements = obj.to_measurements(
            meas_data={"./data/m0.csv": data},
            units={
                "u1": convert_unit("mmol / l"),
                "u2": convert_unit("mmol / l"),
                "u3": convert_unit("mmol / l"),
                "u4": convert_unit("mmol / l"),
            },
        )

        # Assert
        assert len(obj.formats) == 1, "Expected 1 format"
        assert len(obj.measurements) == 1, "Expected 1 measurement"
        assert len(obj.files) == 1, "Expected 1 file"

        # Assert transformed data
        meas = measurements[0]
        expected_species = {
            "s0": 20.0,
            "s1": 10.0,
            "s2": 0.0,
            "s3": 2.0,
            "p0": 0.0002,
        }

        assert meas.id == "m0", "Expected id 'm0'"
        assert meas.name == "Cephalexin synthesis 1", (
            "Expected name 'Cephalexin synthesis 1'"
        )

        for species, initial in expected_species.items():
            species_data = meas.filter_species_data(species_id=species)

            assert len(species_data) == 1, f"Expected 1 species data for {species}"

            species_data = species_data[0]

            assert species_data.initial == initial, (
                f"Expected initial concentration {initial} for {species}"
            )

            if species == "p0":
                assert len(species_data.data) == 0, f"Expected no values for {species}"
            else:
                assert len(species_data.time) == 10, "Expected 10 time points"
                assert len(species_data.data) == 10, f"Expected 10 values for {species}"
