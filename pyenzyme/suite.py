import json

import httpx
import rich

import pyenzyme as pe


class EnzymeMLSuite:
    """
    A suite for interacting with the EnzymeML service.

    Attributes:
        client (httpx.Client): The HTTP client for making requests to the EnzymeML service.
    """

    def __init__(self, url: str = "http://localhost:13452"):
        """
        Initializes the EnzymeMLSuite with a base URL for the EnzymeML service.
        """
        self.client = httpx.Client(base_url=url)

    def get_current(self) -> pe.EnzymeMLDocument:
        """
        Retrieves the current EnzymeML document from the service.

        Returns:
            EnzymeMLDocument: The current EnzymeML document.

        Raises:
            httpx.HTTPStatusError: If the request to the service fails.
        """

        try:
            response = self.client.get("/docs/:current")
        except httpx.ConnectError:
            raise ConnectionError(
                "Could not connect to the EnzymeML suite. Make sure it is running."
            )

        response.raise_for_status()

        content = response.json()["data"]["content"]

        return pe.read_enzymeml_from_string(content)

    def update_current(self, doc: pe.EnzymeMLDocument):
        """
        Updates the current EnzymeML document on the service.

        Args:
            doc (EnzymeMLDocument): The EnzymeML document to update.

        Raises:
            httpx.HTTPStatusError: If the request to the service fails.
        """
        try:
            response = self.client.put(
                "/docs/:current",
                json=json.loads(doc.model_dump_json()),
            )
        except httpx.ConnectError:
            raise ConnectionError(
                "Could not connect to the EnzymeML suite. Make sure it is running."
            )

        response.raise_for_status()

        rich.print("[bold green]Document updated successfully![/]")
