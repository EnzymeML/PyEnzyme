import pyenzyme as pe


def _get_unit(unit_id: str, units: dict[str, pe.UnitDefinition]) -> str | None:
    """
    Get the unit from an EnzymeML unit definition.
    """

    if unit_id not in units:
        return None

    return units[unit_id].model_dump_json()
