from pyenzyme.sbml.versions.v2 import (
    DataAnnot,
    MeasurementAnnot,
    ConditionsAnnot,
    SpeciesDataAnnot,
    TemperatureAnnot,
    PHAnnot,
    SmallMoleculeAnnot,
    ProteinAnnot,
    ParameterAnnot,
    VariablesAnnot,
    VariableAnnot,
)


class TestSBMLAnnotsV2:
    def test_equation_variables(self):
        # Arrange
        xml_string = """
            <enzymeml:variables xmlns:enzymeml="https://www.enzymeml.org/v2">
                <enzymeml:variable id="s0" name="s0" symbol="s0"/>
                <enzymeml:variable id="s1" name="s1" symbol="s1"/>
            </enzymeml:variables>
        """

        # Act
        variables = VariablesAnnot.from_xml(xml_string)

        # Assert
        expected = VariablesAnnot(
            variables=[
                VariableAnnot(
                    id="s0",
                    name="s0",
                    symbol="s0",
                ),
                VariableAnnot(
                    id="s1",
                    name="s1",
                    symbol="s1",
                ),
            ],
        )

        assert variables.model_dump() == expected.model_dump(), (
            "Variables annotation was not parsed correctly"
        )

    def test_parameter_annot(self):
        # Arrange
        xml_string = """
            <enzymeml:parameter xmlns:enzymeml="https://www.enzymeml.org/v2">
                <enzymeml:lowerBound>0.0</enzymeml:lowerBound>
                <enzymeml:upperBound>100.0</enzymeml:upperBound>
                <enzymeml:stdDeviation>0.1</enzymeml:stdDeviation>
            </enzymeml:parameter>
        """

        # Act
        parameter = ParameterAnnot.from_xml(xml_string)

        # Assert
        expected = ParameterAnnot(
            lower_bound=0.0,
            upper_bound=100.0,
            stderr=0.1,
        )

        assert parameter.model_dump() == expected.model_dump(), (
            "Parameter annotation was not parsed correctly"
        )

    def test_protein_annot(self):
        # Arrange
        xml_string = """
            <enzymeml:protein xmlns:enzymeml="https://www.enzymeml.org/v2">
                <enzymeml:ecnumber>1.1.1.1</enzymeml:ecnumber>
                <enzymeml:organism>E.coli</enzymeml:organism>
                <enzymeml:organismTaxId>12345</enzymeml:organismTaxId>
                <enzymeml:sequence>MTEY</enzymeml:sequence>
            </enzymeml:protein>
        """

        # Act
        protein = ProteinAnnot.from_xml(xml_string)

        # Assert
        expected = ProteinAnnot(
            ecnumber="1.1.1.1",
            organism="E.coli",
            organism_tax_id="12345",
            sequence="MTEY",
        )

        assert protein.model_dump() == expected.model_dump(), (
            "Protein annotation was not parsed correctly"
        )

    def test_small_mol_annot(self):
        # Arrange
        xml_string = """
            <enzymeml:smallMolecule xmlns:enzymeml="https://www.enzymeml.org/v2">
                <enzymeml:inchiKey>QTBSBXVTEAMEQO-UHFFFAOYSA-N</enzymeml:inchiKey>
                <enzymeml:smiles>CC(=O)O</enzymeml:smiles>
            </enzymeml:smallMolecule>
        """

        # Act
        small_molecule = SmallMoleculeAnnot.from_xml(xml_string)

        # Assert
        expected = SmallMoleculeAnnot(
            inchikey="QTBSBXVTEAMEQO-UHFFFAOYSA-N",
            canonical_smiles="CC(=O)O",
        )

        assert small_molecule.model_dump() == expected.model_dump(), (
            "Small molecule annotation was not parsed correctly"
        )

    def test_data_annot(self):
        # Arrange
        xml_string = """
            <enzymeml:data xmlns:enzymeml="https://www.enzymeml.org/v2" file="data.tsv">
            <enzymeml:measurement id="m0" name="m0" timeUnit="u1">
              <enzymeml:conditions>
                <enzymeml:ph value="7.0"/>
                <enzymeml:temperature value="298.15" unit="u3"/>
              </enzymeml:conditions>
              <enzymeml:speciesData species="s0" unit="u2" type="CONCENTRATION"/>
              <enzymeml:speciesData species="s1" value="10.0" unit="u2" type="CONCENTRATION"/>
            </enzymeml:measurement>
            <enzymeml:measurement id="m1" name="m1" timeUnit="u1">
              <enzymeml:conditions>
                <enzymeml:ph value="7.0"/>
                <enzymeml:temperature value="298.15" unit="u3"/>
              </enzymeml:conditions>
              <enzymeml:speciesData species="s0" unit="u2" type="CONCENTRATION"/>
              <enzymeml:speciesData species="s1" value="10.0" unit="u2" type="CONCENTRATION"/>
            </enzymeml:measurement>
          </enzymeml:data>
        """

        # Act
        data = DataAnnot.from_xml(xml_string)

        # Assert
        expected = DataAnnot(
            file="data.tsv",
            measurements=[
                MeasurementAnnot(
                    id="m0",
                    name="m0",
                    time_unit="u1",
                    conditions=ConditionsAnnot(
                        ph=PHAnnot(
                            value=7.0,
                        ),
                        temperature=TemperatureAnnot(
                            value=298.15,
                            unit="u3",
                        ),
                    ),
                    species_data=[
                        SpeciesDataAnnot(
                            species_id="s0",
                            unit="u2",
                            type="CONCENTRATION",
                        ),
                        SpeciesDataAnnot(
                            species_id="s1",
                            initial=10.0,
                            unit="u2",
                            type="CONCENTRATION",
                        ),
                    ],
                ),
                MeasurementAnnot(
                    id="m1",
                    name="m1",
                    time_unit="u1",
                    conditions=ConditionsAnnot(
                        ph=PHAnnot(
                            value=7.0,
                        ),
                        temperature=TemperatureAnnot(
                            value=298.15,
                            unit="u3",
                        ),
                    ),
                    species_data=[
                        SpeciesDataAnnot(
                            species_id="s0",
                            unit="u2",
                            type="CONCENTRATION",
                        ),
                        SpeciesDataAnnot(
                            species_id="s1",
                            initial=10.0,
                            unit="u2",
                            type="CONCENTRATION",
                        ),
                    ],
                ),
            ],
        )

        assert data.model_dump() == expected.model_dump(), (
            "Data annotation was not parsed correctly"
        )
