from abc import ABC, abstractmethod
from typing import Union

from pyenzyme.enzymeml.core.enzymemldocument import EnzymeMLDocument


class BaseThinLayer(ABC):

    def __init__(self, path, measurement_ids: Union[str, list] = "all"):

        if isinstance(measurement_ids, str) and measurement_ids != "all":
            raise TypeError(
                "Measurements must either be a list of IDs or 'all'"
            )

        # Load the EnzymeML document to gather data
        self.enzmldoc = EnzymeMLDocument.fromFile(path)

        # The following will extract the tim course data found in all measurements
        self.sbml_xml = self.enzmldoc.toXMLString()
        self.data = self.enzmldoc.exportMeasurementData(
            measurement_ids=measurement_ids
        )

        # Get all rate laws and store them in a dictionary
        self.reaction_data = {
            reaction.id: (reaction.model,
                          reaction.getStoichiometricCoefficients())
            for reaction in self.enzmldoc.reaction_dict.values()
        }

    @abstractmethod
    def optimize(self) -> EnzymeMLDocument:
        """
        The optimize method should only utilize the objects attributes 'data' and 'models' since these
        should cover all necessary informations to run the optimization. In addition, the method could
        also utilize the XML string if based in SBML.

        Finally, if an optimization has been performed the method should enter all estimated values as
        well as optional statistics such as stdev or AKAIKE for instance to each parameter. Since the
        models found in 'self.models' are immutable objects and thus references, the estimated parameters
        will already be inserted to the model.

        See the example class below to see how the optimization could be implemented.
        """


class ModelingTool(BaseThinLayer):

    def optimize(self):
        """
        This is an example of how a thin layer could be built using the ABC class 'BaseThinLayer'

        Feel free to include specific options in this method such that your application can be
        used properly.
        """

        for reaction_id, (model, stoich_coeffs) in self.reaction_data.items():

            """
            This is an example of how individual fields could be entered and used in a
            modeling environment. Note that the model holds all informations on the parameters
            as well as the mathematical equation itself.
            """

            print("<<< Acccessing the model >>>")
            print(model.equation)
            for parameter in model.parameters:
                print(parameter.dict())

            print("<<< Acccessing stoichiometry >>>")
            for species_id, stoichiometry in stoich_coeffs.items():
                print(species_id, stoichiometry)

        """
        Data is provided as a dictionary holding each initial concentration inside the "initConc" key
        as well as the time course data for all species in the key "data". Every header in the DataFrame
        is named by a patter (replicate ID | species ID | unit)
        """

        print("<<< Data >>>")
        print(self.data["m0"]["initConc"])
        print(self.data["m0"]["data"])

        """
        In order to write everything back to the EnzymeML document, simply fetch the desired parameters of
        a reaction and set the value attribute or any other one and return the EnyzmeML document.
        
        Here the first reaction will be equipped with toy values for the sake of demonstration.
        """

        model, _ = self.reaction_data["r0"]

        print("<<< Before assignement >>>")
        print(model.json(indent=2))

        for parameter in model.parameters:
            parameter.value = 100.0

        print("<<< After assignement >>>")
        print(model.json(indent=2))


def main():
    thin_layer = ModelingTool(
        path="examples/ThinLayers/COPASI/3IZNOK_SIMULATED.omex"
    )
    thin_layer.optimize()


if __name__ == "__main__":
    main()
