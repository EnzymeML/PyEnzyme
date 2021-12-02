import os
import shutil

from fastapi import FastAPI
from starlette.responses import FileResponse

from pyenzyme.enzymeml.core.enzymemldocument import EnzymeMLDocument

app = FastAPI()


@app.post("/create")
def create_EnzymeML(enzmldoc: EnzymeMLDocument):

    def _convertUnits(dictionary: dict, key: str):
        """Converts all units to unit_ids and stores them in the model"""
        for obj in dictionary.values():
            unit_string = obj.__dict__.get(key.replace("_id", "")[1::])
            obj.__setattr__(
                key,
                enzmldoc._convertToUnitDef(unit_string)
            )

    # Convert all units
    _convertUnits(enzmldoc.vessel_dict, "_unit_id")
    _convertUnits(enzmldoc.protein_dict, "_unit_id")
    _convertUnits(enzmldoc.reactant_dict, "_unit_id")
    _convertUnits(enzmldoc.reaction_dict, "_temperature_unit_id")

    # Convert all kinetic parameters
    for reaction in enzmldoc.reaction_dict.values():
        if reaction.model is None:
            continue

        params = {
            param.name: param
            for param in reaction.model.parameters
        }

        _convertUnits(params, "_unit_id")

    # Convert measurment units
    for measurement in enzmldoc.measurement_dict.values():
        measurement._global_time_unit_id = enzmldoc._convertToUnitDef(
            measurement.global_time_unit
        )

        proteins = measurement.getProteins()
        reactants = measurement.getReactants()

        _convertUnits({**proteins, **reactants}, "_unit_id")

        # Convert replicates
        all_replicates = {
            replicate.replicate_id: replicate
            for measurement_data in {**proteins, **reactants}.values()
            for replicate in measurement_data.replicates
        }

        _convertUnits(all_replicates, "_data_unit_id")
        _convertUnits(all_replicates, "_time_unit_id")

    # Write the new EnzymeML file
    try:
        dirpath = "."
        file_name = f"{enzmldoc.name.replace(' ', '_')}.omex"
        file_path = os.path.join(
            dirpath,
            file_name
        )

        enzmldoc.toFile(dirpath)

        return FileResponse(file_path, filename=file_name)

    except Exception as e:
        return str(e)

    finally:
        shutil.rmt
