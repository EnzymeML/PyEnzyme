import os

from fastapi import FastAPI, UploadFile, File, Request, Body
from starlette.responses import FileResponse, JSONResponse, HTMLResponse
from starlette.background import BackgroundTasks
from fastapi.templating import Jinja2Templates

from pyenzyme.enzymeml.core.enzymemldocument import EnzymeMLDocument
from pyenzyme.enzymeml.core.measurement import Measurement
from pyenzyme.enzymeml.tools.validator import EnzymeMLValidator
from pyenzyme.utils.rest_examples import create_full_example
from pyenzyme.enzymeml.core.exceptions import (
    MeasurementDataSpeciesIdentifierError,
    ECNumberError,
    ChEBIIdentifierError,
    DataError,
    SpeciesNotFoundError,
    UniProtIdentifierError,
    ParticipantIdentifierError,
)


# * Settings
app = FastAPI(title="PyEnzyme REST-API", version="1.2", docs_url="/")


templates = Jinja2Templates(directory="static")


# * Functions


def remove_file(path: str) -> None:
    os.unlink(path)


# ! Basic operations


@app.post(
    "/create",
    summary="Creates an EnzymeML document based on a JSON body",
    description="Please note, in the schema 'aditionalPropsX' represent the individual IDs of the entities. However, these will not be included, since PyEnzyme takes car for that. Thus, feel free to use any string you like. Returns a binary file, which is an OMEX archive",
    tags=["Basic operations"],
)
async def create_EnzymeML(
    background_tasks: BackgroundTasks,
    enzmldoc: EnzymeMLDocument = Body(..., example=create_full_example()),
):

    # Recreate the EnzymeML document
    nu_enzmldoc = EnzymeMLDocument.fromJSON(enzmldoc.json())

    # Write the new EnzymeML file
    dirpath = "."
    file_name = f"{nu_enzmldoc.name.replace(' ', '_')}.omex"
    file_path = os.path.join(dirpath, file_name)

    nu_enzmldoc.toFile(dirpath, name=nu_enzmldoc.name)

    try:
        response = FileResponse(file_path, filename=file_name)

        return response

    except Exception as e:
        raise

    finally:
        background_tasks.add_task(remove_file, path=file_name)


def parse_measurement_data(measurement, key, nu_measurement, enzmldoc):
    for measurement_data in measurement.species_dict[key].values():
        nu_measurement.addData(
            init_conc=measurement_data.init_conc,
            unit=measurement_data.unit,
            protein_id=measurement_data.protein_id,
            reactant_id=measurement_data.reactant_id,
        )

        nu_measurement.addReplicates(measurement_data.replicates, enzmldoc=enzmldoc)


@app.post(
    "/upload/dataverse",
    summary="Uploads an OMEX archive to a dataverse installation.",
    description="Use this endpoint as form-data and specify the document to be uploaded via the key 'omex_archive' for a succesfull upload.",
    tags=["Databases"],
)
async def upload_to_dataverse(
    background_tasks: BackgroundTasks,
    dataverse_name: str,
    api_token: str,
    base_url: str,
    omex_archive: UploadFile = File(...),
):

    # Write to file
    file_name = omex_archive.filename
    content = await omex_archive.read()
    with open(file_name, "wb") as file_handle:
        file_handle.write(content)

    # Read EnzymeML document
    try:
        enzmldoc = EnzymeMLDocument.fromFile(file_name)
        enzmldoc.uploadToDataverse(
            dataverse_name=dataverse_name, base_url=base_url, api_token=api_token
        )
    except Exception as e:
        return f"{e.__class__.__name__}: {str(e)}"
    finally:
        background_tasks.add_task(remove_file, path=file_name)


@app.post(
    "/read",
    summary="Reads an EnzymeML document served in an OMEX archive to a JSON representation",
    description="Use this endpoint as form-data and specify the document to be uploaded via the key 'omex_archive' for a succesfull request.",
    tags=["Basic operations"],
)
async def read_enzymeml(
    background_tasks: BackgroundTasks, omex_archive: UploadFile = File(...)
):

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
                "log": ...,
                "unit_dict": ...,
                "file_dict": ...,
                "protein_dict": {"Protein": {"__all__": {"_unit_id"}}},
            },
            by_alias=True,
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
    tags=["Modifications"],
)
async def add_Measurement(
    background_tasks: BackgroundTasks,
    measurement: Measurement,
    omex_archive: UploadFile = File(...),
):

    # Check if the species_dict keys are correct
    for key in measurement.species_dict:
        if key not in ["reactants", "proteins"]:
            return {
                "error": f"Key '{key}' is not valid for species dict. Please use either 'reactants' or 'proteins'"
            }

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
        file_path = os.path.join(dirpath, file_name)

        enzmldoc.toFile(dirpath)

        return FileResponse(file_path, filename=file_name)

    except Exception as e:
        return str(e)

    finally:
        background_tasks.add_task(remove_file, path=file_name)


# ! TEMPLATE


@app.get(
    "/template/download",
    summary="Download the EnzymeML spreadsheet template.",
    tags=["EnzymeML spreadsheet"],
)
async def get_enzymeml_template():
    return FileResponse(
        "./templates/EnzymeML_Template.xlsm", filename="EnzymeML_Template.xlsm"
    )


@app.get(
    "/template/upload",
    summary="HTML website to upload the EnzymeML spreadsheet template and convert it to EnzymeML.",
    tags=["EnzymeML spreadsheet"],
    response_class=HTMLResponse,
)
def upload_enzymeml_template(request: Request):
    return templates.TemplateResponse("template_upload.html", {"request": request})


@app.post(
    "/template/convert",
    summary="Converts an EnzymeML spreadsheet template to an EnzymeML document.",
    tags=["EnzymeML spreadsheet"],
)
async def convert_template(
    background_tasks: BackgroundTasks, enzymeml_template: UploadFile = File(...)
):

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
        file_path = os.path.join(dirpath, enzml_name)

        enzmldoc.toFile(dirpath)

        return FileResponse(file_path, filename=enzml_name)

    except Exception as e:
        return str(e)

    finally:
        background_tasks.add_task(remove_file, path=enzml_name)


# ! Validation


@app.get(
    "/validation/download",
    summary="Download the EnzymeML Validation template.",
    tags=["EnzymeML Validation"],
)
async def get_validation_template():
    return FileResponse(
        "templates/EnzymeML_Validation_Template.xlsx",
        filename="EnzymeML_Validation_Template.xlsm",
    )


@app.get(
    "/validation/upload",
    summary="HTML site to upload the EnzymeML Validation template and convert it to a YAML file.",
    tags=["EnzymeML Validation"],
    response_class=HTMLResponse,
)
def upload_validation_template(request: Request):
    return templates.TemplateResponse("validation_upload.html", {"request": request})


@app.post(
    "/validation/convert",
    summary="Convert the EnzymeML Validation template to a YAML template to use for validation on server site.",
    tags=["EnzymeML Validation"],
)
async def convert_validation_template(
    background_tasks: BackgroundTasks, validation_template: UploadFile = File(...)
):

    # Write to file
    file_name = validation_template.filename
    content = await validation_template.read()
    with open(file_name, "wb") as file_handle:
        file_handle.write(content)

    # Generate the new EnzymeML file
    try:
        EnzymeMLValidator.convertSheetToYAML(
            path=file_name,
            filename="validation",
        )

        return FileResponse(
            "validation.yaml", filename="EnzymeML_Validation_Template.yaml"
        )

    except Exception as e:
        return str(e)

    finally:
        background_tasks.add_task(remove_file, path=file_name)
        background_tasks.add_task(remove_file, path="validation.yaml")


@app.post(
    "/validation/",
    summary="Vaidates an EnzymeML document based on a given EnzymeML Validation YAML file. Returns a boolean and a report, if validation has failed.",
    tags=["EnzymeML Validation"],
)
async def validate_enzymeml(
    background_tasks: BackgroundTasks,
    omex_archive: UploadFile = File(...),
    validation_template: UploadFile = File(...),
):

    # Write EnzymeML to file
    omex_name = omex_archive.filename
    content = await omex_archive.read()
    with open(omex_name, "wb") as file_handle:
        file_handle.write(content)

    # Read EnzymeML document
    try:
        enzmldoc = EnzymeMLDocument.fromFile(omex_name)
    except Exception as e:
        return f"{e.__class__.__name__}: {str(e)}"
    finally:
        background_tasks.add_task(remove_file, path=omex_name)

    # Write YAML to file
    valid_name = validation_template.filename
    content = await validation_template.read()
    with open(valid_name, "wb") as file_handle:
        file_handle.write(content)

    # Read YAML and validate accordingly
    try:
        report, is_valid = enzmldoc.validateDocument(yaml_path=valid_name)

        return {"is_valid": is_valid, "report": report}
    finally:
        background_tasks.add_task(remove_file, path=valid_name)


# * Exception handlers


@app.exception_handler(MeasurementDataSpeciesIdentifierError)
async def handle_meas_species_id_error(
    req: Request, exc: MeasurementDataSpeciesIdentifierError
):
    return JSONResponse(status_code=406, content={"message": str(exc)})


@app.exception_handler(ECNumberError)
async def handle_ecnumber_error(req: Request, exc: ECNumberError):
    return JSONResponse(status_code=406, content={"message": str(exc)})


@app.exception_handler(ChEBIIdentifierError)
async def handle_chebi_error(req: Request, exc: ChEBIIdentifierError):
    return JSONResponse(status_code=406, content={"message": str(exc)})


@app.exception_handler(DataError)
async def handle_data_error(req: Request, exc: DataError):
    return JSONResponse(status_code=406, content={"message": str(exc)})


@app.exception_handler(SpeciesNotFoundError)
async def handle_species_error(req: Request, exc: SpeciesNotFoundError):
    return JSONResponse(status_code=406, content={"message": str(exc)})


@app.exception_handler(UniProtIdentifierError)
async def handle_uniprotid_error(req: Request, exc: UniProtIdentifierError):
    return JSONResponse(status_code=406, content={"message": str(exc)})


@app.exception_handler(ParticipantIdentifierError)
async def handle_participant_error(req: Request, exc: ParticipantIdentifierError):
    return JSONResponse(status_code=406, content={"message": str(exc)})
