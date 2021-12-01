from fastapi import FastAPI

from pyenzyme.enzymeml.core.unitdef import UnitDef
from pyenzyme.enzymeml.core.enzymemldocument import EnzymeMLDocument
from pyenzyme.enzymeml.core.enzymemlbase import EnzymeMLBase

app = FastAPI()


@app.post("/create")
def create_EnzymeML(enzmldoc: EnzymeMLDocument):
    return {"WORKS"}
