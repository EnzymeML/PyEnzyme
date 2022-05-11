from pyenzyme.enzymeml.models.kineticmodel import KineticModel
from pyenzyme.enzymeml.models.kineticmodel import KineticParameter
from pyenzyme.enzymeml.core.ontology import SBOTerm


class TestKineticModel:
    def test_content(self):
        """Tests consistency of content"""

        # Set up kinetic parameter
        param = KineticParameter(
            name="kcat",
            value=10.0,
            unit="1 / s",
            initial_value=20.0,
            upper=30.0,
            lower=0,
            is_global=False,
            stdev=1.0,
        )

        assert param.name == "kcat"
        assert param.value == 10.0
        assert param.unit == "1 / s"
        assert param.initial_value == 20.0
        assert param.upper == 30.0
        assert param.lower == 0.0
        assert param.stdev == 1.0
        assert not param.is_global

        # Set up kinetic model
        km = KineticModel(
            name="Michaelis Menten Model",
            equation="p0*kcat*s0 / (km * s0)",
            parameters=[param],
            ontology=SBOTerm.MICHAELIS_MENTEN,
        )

        assert km.name == "Michaelis Menten Model"
        assert km.equation == "p0*kcat*s0 / (km * s0)"
        assert km.ontology == SBOTerm.MICHAELIS_MENTEN

        # Add another paramete
        km.addParameter(
            name="km",
            value=10.0,
            unit="mmole / l",
            initial_value=20.0,
            upper=30.0,
            lower=0,
            is_global=False,
            stdev=1.0,
        )

        # Check addition has worked
        assert km.getParameter("km").name == "km"
        assert km.getParameter("km").value == 10.0
        assert km.getParameter("km").unit == "mmole / l"
        assert km.getParameter("km").initial_value == 20.0
        assert km.getParameter("km").upper == 30.0
        assert km.getParameter("km").lower == 0.0
        assert km.getParameter("km").stdev == 1.0
        assert not km.getParameter("km").is_global

    def test_from_equation(self, enzmldoc):
        """Tests the model initialization via an equation"""

        # With IDs
        model = KineticModel.fromEquation(name="Model", equation="s0 * x + p0 * c0")

        assert len(model.parameters) == 1
        assert model.parameters[0].name == "x"
        assert model.name == "Model"

        # With names
        model = KineticModel.fromEquation(
            name="Model", equation="Reactant * x + Protein * Complex", enzmldoc=enzmldoc
        )

        assert len(model.parameters) == 1
        assert model.parameters[0].name == "x"
        assert model.name == "Model"
        assert model.equation == "s0 * x + p0 * c0"

    def test_model_generator(self, enzmldoc):
        """Tests consistency of the model generator"""

        # Set up a generator
        generator = KineticModel.createGenerator(
            name="Michaelis Menten Model",
            equation="protein*kcat*substrate / (km * substrate)",
            kcat={"unit": "1 / s", "value": 10.0},
            km={"unit": "mmole / l", "value": 10.0},
        )

        # Generate kinetic model
        km = generator(protein="p0", substrate="s0")

        assert km.name == "Michaelis Menten Model"
        assert km.equation == "'p0'*kcat*'s0' / (km * 's0')"

        # Add model to reaction
        reaction = enzmldoc.reaction_dict["r0"]
        reaction.setModel(km, enzmldoc)

        assert reaction.model.name == "Michaelis Menten Model"
        assert reaction.model.equation == "p0*kcat*s0 / (km * s0)"

        # Add model to reaction
        reaction.model = km

        assert reaction.model.name == "Michaelis Menten Model"
        assert reaction.model.equation == "p0*kcat*s0 / (km * s0)"

        # Test if the model is actually written to the XML
        xml_string = enzmldoc.toXMLString()
        expected = """<math xmlns="http://www.w3.org/1998/Math/MathML">
            <apply>
              <divide/>
              <apply>
                <times/>
                <ci> p0 </ci>
                <ci> kcat </ci>
                <ci> s0 </ci>
              </apply>
              <apply>
                <times/>
                <ci> km </ci>
                <ci> s0 </ci>
              </apply>
            </apply>
          </math>"""

        assert expected in xml_string, "Model has not been written to XML"
