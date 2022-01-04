import os

from fastapi import FastAPI, UploadFile, File
from starlette.responses import FileResponse, RedirectResponse
from starlette.background import BackgroundTasks

from pyenzyme.enzymeml.core.enzymemldocument import EnzymeMLDocument
from pyenzyme.enzymeml.core.measurement import Measurement

app = FastAPI(title="PyEnzyme REST-API", version="1.2", docs_url="/")

# * Functions


def remove_file(path: str) -> None:
    os.unlink(path)

# ! Basic operations


@app.post(
    "/create",
    summary="Creates an EnzymeML document based on a JSON body",
    description="Please note, in the schema 'aditionalPropsX' represent the individual IDs of the entities. However, these will not be included, since PyEnzyme takes car for that. Thus, feel free to use any string you like. Returns a binary file, which is an OMEX archive",
    tags=["Basic operations"]
)
async def create_EnzymeML(enzmldoc: EnzymeMLDocument, background_tasks: BackgroundTasks):

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
        background_tasks.add_task(remove_file, path=file_name)


@app.post(
    "/read",
    summary="Reads an EnzymeML document served in an OMEX archive to a JSON representation",
    description="Use this endpoint as form-data and specify the document to be uploaded via the key 'omex_archive' for a succesfull request.",
    tags=["Basic operations"]
)
async def read_enzymeml(background_tasks: BackgroundTasks, omex_archive: UploadFile = File(...)):

    # Write to file
    file_name = omex_archive.filename
    content = await omex_archive.read()
    with open(file_name, "wb") as file_handle:
        file_handle.write(content)

    # Read EnzymeML document
    try:
        enzmldoc = EnzymeMLDocument.fromFile(file_name)
        return enzmldoc.dict(
            exclude_none=True,
            exclude={
                "unit_dict": ...,
                "file_dict": ...,
                "protein_dict":
                    {
                        "Protein": {"__all__": {"_unit_id"}}
                    }
            },
            by_alias=True
        )
    except Exception as e:
        return f"{e.__class__.__name__}: {str(e)}"
    finally:
        background_tasks.add_task(remove_file, path=file_name)

# ! Modifications


@app.post(
    "/add_measurement",
    summary="Adds a measurement to an existing EnzymeML document",
    description="By using this endpoint, you can add successive raw data without having to create a new EnzymeML dcoument. Returns a binary file, which is an OMEX Archive",
    tags=["Modifications"]
)
async def add_Measurement(
    background_tasks: BackgroundTasks,
    measurement: Measurement,
    omex_archive: UploadFile = File(...)
):

    # Check if the species_dict keys are correct
    for key in measurement.species_dict:
        if key not in ["reactants", "proteins"]:
            return {"error": f"Key '{key}' is not valid for species dict. Please use either 'reactants' or 'proteins'"}

    # Write to file
    file_name = omex_archive.filename
    content = await omex_archive.read()
    with open(file_name, "wb") as file_handle:
        file_handle.write(content)

    # Read EnzymeML document
    enzmldoc = EnzymeMLDocument.fromFile(file_name)

    # Add the measurement
    enzmldoc.addMeasurement(measurement)

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
        background_tasks.add_task(remove_file, path=file_name)

# ! TOOLS


@app.get(
    "/template/download",
    summary="Download the EnzymeML spreadsheet template.",
    tags=["EnzymeML spreadsheet"]
)
async def get_enzymeml_template():
    return FileResponse("./templates/EnzymeML_Template.xlsm", filename="EnzymeML_Template.xlsm")


@app.post(
    "/template/convert",
    summary="Converts an EnzymeML spreadsheet template to an EnzymeML document.",
    tags=["EnzymeML spreadsheet"]
)
async def convert_template(background_tasks: BackgroundTasks, enzymeml_template: UploadFile = File(...)):

    # Write to file
    file_name = enzymeml_template.filename
    content = await enzymeml_template.read()
    with open(file_name, "wb") as file_handle:
        file_handle.write(content)

    # Generate the new EnzymeML file
    try:
        enzmldoc = EnzymeMLDocument.fromTemplate(file_name)

    except Exception as e:
        return str(e)

    finally:
        background_tasks.add_task(remove_file, path=file_name)

    # Write the new EnzymeML file
    try:
        dirpath = "."
        enzml_name = f"{enzmldoc.name.replace(' ', '_')}.omex"
        file_path = os.path.join(
            dirpath,
            enzml_name
        )

        enzmldoc.toFile(dirpath)

        return FileResponse(file_path, filename=enzml_name)

    except Exception as e:
        return str(e)

    finally:
        background_tasks.add_task(remove_file, path=enzml_name)
