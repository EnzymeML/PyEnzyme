from typing import Any
from pydantic import BaseModel, ConfigDict


class BaseRow(BaseModel):
    """
    Base class for all PEtab rows.
    """

    model_config = ConfigDict(use_enum_values=True)

    def to_row(self) -> dict[str, Any]:
        """
        Converts the row to a dictionary suitable for a PEtab table row.
        """
        return self.model_dump(by_alias=True, mode="json")
