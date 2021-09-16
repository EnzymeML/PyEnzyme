DataverseMapping = {
    "Creators": {
        "family_name": {
            "typeName": "authorName",
            "multiple": False,
            "typeClass": "primitive"
        },
        "mail": {
            "typeName": "datasetContactEmail",
            "multiple": False,
            "typeClass": "primitive"
        }
    },
    "Vessel": {
        "name": {
            "typeName": "enzymeMLVesselName",
            "multiple": False,
            "typeClass": "primitive"
        },
        "size": {
            "typeName": "enzymeMLVesselSize",
            "multiple": False,
            "typeClass": "primitive"
        },
        "unit": {
            "typeName": "enzymeMLVesselUnit",
            "multiple": False,
            "typeClass": "controlledVocabulary"
        },
        "constant": {
            "typeName": "enzymeMLVesselConstant",
            "multiple": False,
            "typeClass": "controlledVocabulary"
        }
    },
    "Reactant": {
        "name": {
            "typeName": "enzymeMLReactantName",
            "multiple": False,
            "typeClass": "primitive"
        },
        "vessel": {
            "typeName": "enzymeMLReactantVessel",
            "multiple": False,
            "typeClass": "primitive"
        },
        "init_conc": {
            "typeName": "enzymeMLReactantInitialConcentration",
            "multiple": False,
            "typeClass": "primitive"
        },
        "substanceunits": {
            "typeName": "enzymeMLReactantSubstanceUnits",
            "multiple": False,
            "typeClass": "controlledVocabulary"
        },
        "constant": {
            "typeName": "enzymeMLReactantConstant",
            "multiple": False,
            "typeClass": "controlledVocabulary"
        },
        "sboterm": {
            "typeName": "enzymeMLReactantSBOTerm",
            "multiple": False,
            "typeClass": "primitive"
        }
        # "id": {
        #     "typeName": "enzymeMLReactantID",
        #     "multiple": False,
        #     "typeClass": "primitive"
        # }
    },
    "Protein": {
        "name": {
            "typeName": "enzymeMLProteinName",
            "multiple": False,
            "typeClass": "primitive"
        },
        "sequence": {
            "typeName": "enzymeMLProteinSequence",
            "multiple": False,
            "typeClass": "primitive"
        },
        "constant": {
            "typeName": "enzymeMLProteinConstant",
            "multiple": False,
            "typeClass": "controlledVocabulary"
        },
        "sboterm": {
            "typeName": "enzymeMLProteinSBOTerm",
            "multiple": False,
            "typeClass": "primitive"
        },
        "vessel": {
            "typeName": "enzymeMLProteinVessel",
            "multiple": False,
            "typeClass": "primitive"
        },
        "init_conc": {
            "typeName": "enzymeMLProteinInitialConcentration",
            "multiple": False,
            "typeClass": "primitive"
        },
        "substanceunits": {
            "typeName": "enzymeMLProteinSubstanceUnit",
            "multiple": False,
            "typeClass": "controlledVocabulary"
        }
        # "id": {
        #     "typeName": "enzymeMLProteinID",
        #     "multiple": False,
        #     "typeClass": "primitive"
        # }
    },
    "Reaction": {
        "name": {
            "typeName": "enzymeMLReactionName",
            "multiple": False,
            "typeClass": "primitive"
        },
        "temperature": {
            "typeName": "enzymeMLReactionTemperatureValue",
            "multiple": False,
            "typeClass": "primitive"
        },
        "tempunit": {
            "typeName": "enzymeMLReactionTemperatureUnit",
            "multiple": False,
            "typeClass": "controlledVocabulary"
        },
        "ph": {
            "typeName": "enzymeMLReactionpH",
            "multiple": False,
            "typeClass": "primitive"
        },
        "educts": {
            "typeName": "enzymeMLReactionEduct",
            "multiple": False,
            "typeClass": "primitive"
        },
        "modifiers": {
            "typeName": "enzymeMLReactionModifier",
            "multiple": False,
            "typeClass": "primitive"
        },
        "products": {
            "typeName": "enzymeMLReactionProduct",
            "multiple": False,
            "typeClass": "primitive"
        }
    },
    "KineticLaw": {
        "name": {
            "typeName": "enzymeMLKineticLawName",
            "multiple": False,
            "typeClass": "primitive"
        },
        "equation": {
            "typeName": "enzymeMLKineticLawEquation",
            "multiple": False,
            "typeClass": "primitive"
        },
        "reaction": {
            "typeName": "enzymeMLKineticLawReaction",
            "multiple": False,
            "typeClass": "primitive"
        }
    },
    "KineticParameter": {
        "name": {
            "typeName": "enzymeMLKineticParameterName",
            "multiple": False,
            "typeClass": "primitive"
        },
        "value": {
            "typeName": "enzymeMLKineticParameterValue",
            "multiple": False,
            "typeClass": "primitive"
        },
        "unit": {
            "typeName": "enzymeMLKineticParameterUnit",
            "multiple": False,
            "typeClass": "primitive"
        }
    }
}
