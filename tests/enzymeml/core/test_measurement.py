import pytest

from pyenzyme.enzymeml.core.measurement import Measurement


class TestMeasurement:
    def test_content(self):
        """Tests consistency of content"""

        measurement = Measurement(
            name="SomeMeasurement",
            temperature=100.0,
            temperature_unit="C",
            ph=7.0,
            global_time=[1, 2, 3, 4],
            global_time_unit="s",
            id="m0",
            uri="URI",
            creator_id="a0",
        )

        assert measurement.name == "SomeMeasurement"
        assert measurement.temperature == 100.0 + 273.15
        assert measurement.temperature_unit == "K"
        assert measurement.ph == 7.0
        assert measurement.global_time == [1, 2, 3, 4]
        assert measurement.global_time_unit == "s"
        assert measurement.id == "m0"
        assert measurement.uri == "URI"
        assert measurement.creator_id == "a0"
        assert measurement.species_dict == {"proteins": {}, "reactants": {}}
        assert not measurement._global_time_unit_id
        assert not measurement._temperature_unit_id

    def test_defaults(self):
        """Test default values"""

        measurement = Measurement(name="SomeMeasurement")

        assert not measurement.temperature
        assert not measurement.temperature_unit
        assert not measurement.ph
        assert not measurement.global_time
        assert not measurement.global_time_unit
        assert not measurement.id
        assert not measurement.uri
        assert not measurement.creator_id
        assert measurement.species_dict == {"proteins": {}, "reactants": {}}

    def test_data_export(self, measurement):
        """Test correct data export"""

        # Call the export function
        data = measurement.exportData()

        # Check structure
        assert "proteins" in data.keys()
        assert "reactants" in data.keys()

        # Check initial concentrations
        init_conc = data["proteins"]["initConc"]
        assert init_conc == {"p0": (10.0, "mmole / l")}

        init_conc = data["reactants"]["initConc"]
        assert init_conc == {"s0": (10.0, "mmole / l")}

        # Construct expected DataFrame
        expected_protein = {
            "p0": {0: 1.0, 1: 1.0, 2: 1.0, 3: 1.0},
            "time": {0: 1.0, 1: 2.0, 2: 3.0, 3: 4.0},
        }
        expected_reactant = {
            "s0": {0: 1.0, 1: 1.0, 2: 1.0, 3: 1.0},
            "time": {0: 1.0, 1: 2.0, 2: 3.0, 3: 4.0},
        }

        assert data["reactants"]["data"].to_dict() == expected_reactant
        assert data["proteins"]["data"].to_dict() == expected_protein

    def test_data_export_no_repls(self, measurement):
        """Tests export method when no replicates are given"""

        # Remove replicates
        measurement.species_dict["proteins"]["p0"].replicates = []
        measurement.species_dict["reactants"]["s0"].replicates = []

        # Call the export function
        data = measurement.exportData()

        # Check initial concentrations
        init_conc = data["proteins"]["initConc"]
        assert init_conc == {"p0": (10.0, "mmole / l")}

        init_conc = data["reactants"]["initConc"]
        assert init_conc == {"s0": (10.0, "mmole / l")}

        assert not data["reactants"]["data"].to_dict()
        assert not data["proteins"]["data"].to_dict()

    def test_data_export_specific_species(self, measurement):
        """Tests export method when a specific species is given"""

        # Test case with list as argument
        data = measurement.exportData(species_ids=["s0"])
        expected_reactant = {
            "s0": {0: 1.0, 1: 1.0, 2: 1.0, 3: 1.0},
            "time": {0: 1.0, 1: 2.0, 2: 3.0, 3: 4.0},
        }

        assert data["reactants"]["initConc"] == {"s0": (10.0, "mmole / l")}
        assert data["reactants"]["data"].to_dict() == expected_reactant

        assert not data["proteins"]["initConc"]
        assert not data["proteins"]["data"].to_dict()

        # Test case with string as argument
        data = measurement.exportData(species_ids="s0")
        init_conc = data["reactants"]["initConc"]
        expected_reactant = {
            "s0": {0: 1.0, 1: 1.0, 2: 1.0, 3: 1.0},
            "time": {0: 1.0, 1: 2.0, 2: 3.0, 3: 4.0},
        }

        assert data["reactants"]["initConc"] == {"s0": (10.0, "mmole / l")}
        assert data["reactants"]["data"].to_dict() == expected_reactant

        assert not data["proteins"]["initConc"]
        assert not data["proteins"]["data"].to_dict()

    def test_add_replicates(self, measurement, replicate, enzmldoc):
        """Tests the addition of replicates"""

        # Reset replicates
        measurement.species_dict["reactants"]["s0"].replicates = []

        # Call the addReplicates method to add replicate
        measurement.addReplicates(replicate, enzmldoc)

        assert measurement.species_dict["reactants"]["s0"].replicates[0] == replicate

        # Test case with list of replicates
        measurement.species_dict["reactants"]["s0"].replicates = []
        replicate2 = replicate.copy()
        replicate2.id = "repl_s0_1"

        # Call the addReplicates method to add replicate
        measurement.addReplicates([replicate, replicate2], enzmldoc)

        assert measurement.species_dict["reactants"]["s0"].replicates == [
            replicate,
            replicate2,
        ]

    def test_add_data(self, measurement, replicate):
        """Tests the addition of data"""

        # Reset measurement to have no data
        measurement.species_dict = {"proteins": {}, "reactants": {}}

        # Add reactant data
        measurement.addData(
            init_conc=10.0, unit="mmole / l", reactant_id="s0", replicates=[replicate]
        )

        # Extract the entry
        assert "s0" in measurement.species_dict["reactants"].keys()
        reactant = measurement.species_dict["reactants"]["s0"]

        assert reactant.reactant_id == "s0"
        assert reactant.init_conc == 10.0
        assert reactant.unit == "mmole / l"
        assert reactant.replicates == [replicate]

        # Add reactant data
        replicate.species_id = "p0"
        measurement.addData(
            init_conc=10.0, unit="mmole / l", protein_id="p0", replicates=[replicate]
        )

        # Extract the entry
        assert "p0" in measurement.species_dict["proteins"].keys()
        reactant = measurement.species_dict["proteins"]["p0"]

        assert reactant.protein_id == "p0"
        assert reactant.init_conc == 10.0
        assert reactant.unit == "mmole / l"
        assert reactant.replicates == [replicate]

    def test_unit_unification(self, enzmldoc):
        """Tests if unit unification works"""

        # Get the measurement from the EnzymeMLDocument
        measurement = enzmldoc.measurement_dict["m0"]

        # Perform unit unification
        measurement.unifyUnits(kind="mole", scale=-6, enzmldoc=enzmldoc)

        # Check for reactants
        replicate = measurement.species_dict["reactants"]["s0"].replicates[0]
        nu_unit_id = replicate._data_unit_id

        assert replicate.data == [1000.0, 1000.0, 1000.0, 1000.0]
        assert replicate.time == [1.0, 2.0, 3.0, 4.0]
        assert enzmldoc._unit_dict[nu_unit_id].name == "umole / l"

        # Check for proteins
        replicate = measurement.species_dict["proteins"]["p0"].replicates[0]
        nu_unit_id = replicate._data_unit_id

        assert replicate.data == [1000.0, 1000.0, 1000.0, 1000.0]
        assert replicate.time == [1.0, 2.0, 3.0, 4.0]
        assert enzmldoc._unit_dict[nu_unit_id].name == "umole / l"

        # Test for not supported unit kinds
        with pytest.raises(ValueError):
            measurement.unifyUnits(kind="joule", scale=-6, enzmldoc=enzmldoc)

        # Test for not supported unit kinds
        with pytest.raises(ValueError):
            measurement.unifyUnits(kind="mole", scale=-10, enzmldoc=enzmldoc)
