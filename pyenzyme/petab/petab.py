from __future__ import annotations

from pathlib import Path
from typing import List, Union, Optional
from pydantic import BaseModel, ConfigDict, Field


class PEtab(BaseModel):
    """
    PEtab parameter estimation problem config file schema.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    format_version: int = Field(
        default=1,
        description="Version of the PEtab format. Only value 1 is supported.",
    )

    parameter_file: Union[Path, List[Path]] = Field(
        description="File name (absolute or relative) or URL to PEtab parameter table "
        "containing parameters of all models listed in `problems`. A single "
        "table may be split into multiple files and described as an array here."
    )
    problems: List[Problem] = Field(
        default_factory=list,
        description="One or multiple PEtab problems (sets of model, condition, observable "
        "and measurement files). If different model and data files are "
        "independent, they can be specified as separate PEtab problems, which "
        "may allow more efficient handling. Files in one problem cannot refer "
        "to models entities or data specified inside another problem.",
    )

    def add_problem(
        self,
        sbml_files: List[Path],
        measurement_files: List[Path],
        condition_files: List[Path],
        observable_files: List[Path],
        visualization_files: Optional[List[Path]] = None,
    ) -> None:
        """
        Add a problem to the PEtab object.
        """
        self.problems.append(
            Problem(
                sbml_files=sbml_files,
                measurement_files=measurement_files,
                condition_files=condition_files,
                observable_files=observable_files,
                visualization_files=visualization_files,
            )
        )


class Problem(BaseModel):
    """
    A set of PEtab model, condition, observable and measurement files and optional visualization files.
    """

    sbml_files: List[Path] = Field(description="List of PEtab SBML files.")
    measurement_files: List[Path] = Field(
        description="List of PEtab measurement files."
    )
    condition_files: List[Path] = Field(description="List of PEtab condition files.")
    observable_files: List[Path] = Field(description="List of PEtab observable files.")
    visualization_files: Optional[List[Path]] = Field(
        default=None,
        description="List of PEtab visualization files.",
    )


# We need to rebuild the models to ensure
# the correct field names are used.
for cls in [PEtab, Problem]:
    cls.model_rebuild()
