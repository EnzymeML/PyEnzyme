def create_full_example():
    return {
        "name": "Example Document",
        "pubmedid": "00000000",
        "url": "https://www.some-url.com/",
        "doi": "10.1XXX/XXXXXX-XXX-XXXX-X",
        "creators": {
            "a0": {
                "given_name": "Max",
                "family_name": "Mustermann",
                "mail": "max.mustermann@mustermann.com",
            }
        },
        "vessels": {
            "v0": {
                "name": "Tube vessel",
                "volume": 0.015,
                "unit": "l",
                "constant": True,
            }
        },
        "proteins": {
            "p0": {
                "name": "Protein",
                "vessel_id": "v0",
                "init_conc": 5.0,
                "constant": True,
                "unit": "mmole / l",
                "ontology": "SBO:0000252",
                "sequence": "HLPMV",
                "ecnumber": "1.1.1.1",
                "organism": "E.coli",
                "organism_tax_id": "27367",
                "uniprotid": "P02357",
            }
        },
        "complexes": {
            "c0": {
                "name": "Complex",
                "vessel_id": "v0",
                "init_conc": 10.0,
                "constant": False,
                "unit": "mmole / l",
                "ontology": "SBO:0000296",
                "participants": ["s0", "p0"],
            }
        },
        "reactants": {
            "s0": {
                "name": "Reactant",
                "vessel_id": "v0",
                "init_conc": 10.0,
                "constant": False,
                "unit": "mmole / l",
                "ontology": "SBO:0000247",
                "smiles": "[H]O[H]",
                "inchi": "InChI:HJJH",
                "chebi_id": "CHEBI:09823",
            },
            "s1": {
                "name": "oxonium",
                "vessel_id": "v0",
                "init_conc": 10.0,
                "constant": False,
                "unit": "mmole / l",
                "ontology": "SBO:0000247",
                "smiles": "[H][O+]([H])[H]",
                "inchi": "InChI=1S/H2O/h1H2/p+1",
                "chebi_id": "CHEBI:29412",
            },
        },
        "reactions": {
            "r0": {
                "name": "string",
                "reversible": True,
                "temperature": 200,
                "temperature_unit": "K",
                "ph": 7.0,
                "ontology": "SBO:0000176",
                "id": "r0",
                "meta_id": "METAID_R0",
                "model": {
                    "name": "Kinetic Model",
                    "equation": "s0 * x",
                    "parameters": [
                        {
                            "name": "x",
                            "value": 10.0,
                            "unit": "1 / s",
                            "stdev": 0.1,
                            "initial_value": 10.0,
                        }
                    ],
                },
                "educts": [
                    {
                        "species_id": "s0",
                        "stoichiometry": 1.0,
                        "constant": False,
                        "ontology": "SBO:0000015",
                    }
                ],
                "products": [
                    {
                        "species_id": "s1",
                        "stoichiometry": 1.0,
                        "constant": False,
                        "ontology": "SBO:0000011",
                    }
                ],
                "modifiers": [
                    {
                        "species_id": "p0",
                        "stoichiometry": 1.0,
                        "constant": True,
                        "ontology": "SBO:0000013",
                    }
                ],
            }
        },
        "measurements": {
            "m0": {
                "name": "SomeMeasurement",
                "temperature": 4.0,
                "temperature_unit": "K",
                "ph": 7.0,
                "species_dict": {
                    "reactants": {
                        "s0": {
                            "init_conc": 10.0,
                            "unit": "mmole / l",
                            "measurement_id": "m0",
                            "reactant_id": "s0",
                            "replicates": [
                                {
                                    "id": "repl_s0_0",
                                    "species_id": "s0",
                                    "data_type": "conc",
                                    "data_unit": "mmole / l",
                                    "time_unit": "s",
                                    "time": [1.0, 2.0, 3.0, 4.0],
                                    "data": [1.0, 1.0, 1.0, 1.0],
                                    "is_calculated": False,
                                }
                            ],
                        }
                    },
                    "proteins": {
                        "p0": {
                            "init_conc": 10.0,
                            "unit": "mmole / l",
                            "measurement_id": "m0",
                            "protein_id": "p0",
                            "replicates": [
                                {
                                    "id": "repl_p0_0",
                                    "species_id": "p0",
                                    "data_type": "conc",
                                    "data_unit": "mmole / l",
                                    "time_unit": "s",
                                    "time": [1.0, 2.0, 3.0, 4.0],
                                    "data": [1.0, 1.0, 1.0, 1.0],
                                    "is_calculated": False,
                                }
                            ],
                        }
                    },
                },
                "global_time": [1.0, 2.0, 3.0, 4.0],
                "global_time_unit": "s",
                "id": "m0",
            }
        },
    }
