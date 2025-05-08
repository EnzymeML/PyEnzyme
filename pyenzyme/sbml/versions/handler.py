from enum import Enum

from pydantic import BaseModel

from pyenzyme.sbml.versions import v1, v2
from pyenzyme.sbml.versions.v2 import V2Annotation


class SupportedVersions(Enum):
    VERSION1 = "http://sbml.org/enzymeml/version2"
    VERSION2 = "https://www.enzymeml.org/v2"


class VersionHandler(BaseModel):
    version: SupportedVersions

    @classmethod
    def from_uri(cls, uris: set[str]):
        for uri in uris:
            if uri == SupportedVersions.VERSION1.value:
                return cls(version=SupportedVersions.VERSION1)
            if uri == SupportedVersions.VERSION2.value:
                return cls(version=SupportedVersions.VERSION2)

        raise ValueError("No supported version found in URIs")

    def parse_annotation(self, annotation: str) -> v1.V1Annotation | v2.V2Annotation:
        if not annotation:
            return V2Annotation()

        match self.version:
            case SupportedVersions.VERSION1:
                return v1.V1Annotation.from_xml(annotation)
            case SupportedVersions.VERSION2:
                return v2.V2Annotation.from_xml(annotation)
            case _:
                raise ValueError("Unsupported version")

    @staticmethod
    def extract(
        value: v1.V1Annotation | v2.V2Annotation,
        key: str,
    ):
        if not hasattr(value, key):
            raise AttributeError(f"VersionHandler has no attribute '{key}'")

        value = getattr(value, key)

        if value:
            return value.model_dump()
        else:
            return {}
