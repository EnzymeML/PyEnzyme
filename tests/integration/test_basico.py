import tempfile

import pytest
import pyenzyme as pe
from pyenzyme.thinlayers.basico import ThinLayerCopasi
from pyenzyme.versions import v2


class TestCopasiThinLayer:
    def test_optimize(self):
        doc = pe.read_enzymeml("tests/fixtures/modeling/enzmldoc_reaction.json")

        with tempfile.TemporaryDirectory() as tmp_dir:
            layer = ThinLayerCopasi(doc, tmp_dir)
            layer.optimize()

            opt_doc = layer.write()

            k_cat = self._extract_parameter(opt_doc, "k_cat")
            k_ie = self._extract_parameter(opt_doc, "k_ie")
            K_M = self._extract_parameter(opt_doc, "K_M")

            # Check if values are positive using a small epsilon
            expected_km = 82.0
            expected_kcat = 0.85
            expected_kie = 0.0012

            assert k_cat.value is not None, "k_cat is not set"
            assert k_ie.value is not None, "k_ie is not set"
            assert K_M.value is not None, "K_M is not set"

            assert expected_kcat * 0.95 < k_cat.value < expected_kcat * 1.1, (
                f"k_cat is not correct, got {k_cat.value} expected {expected_kcat}"
            )
            assert expected_kie * 0.75 < k_ie.value < expected_kie * 1.1, (
                f"k_ie is not correct, got {k_ie.value} expected {expected_kie}"
            )
            assert expected_km * 0.95 < K_M.value < expected_km * 1.1, (
                f"K_M is not correct, got {K_M.value} expected {expected_km}"
            )

    def test_plot(self):
        doc = pe.read_enzymeml("tests/fixtures/modeling/enzmldoc_reaction.json")

        with tempfile.TemporaryDirectory() as tmp_dir:
            layer = ThinLayerCopasi(doc, tmp_dir)
            layer.optimize()

            fig, axs = pe.plot(
                layer.enzmldoc,
                thinlayer=layer,
                measurement_ids=[
                    "measurement0",
                    "measurement1",
                    "measurement2",
                    "measurement3",
                ],
            )

            # Raw image

            assert fig is not None, "Figure is not created"
            assert axs is not None, "Axes are not created"

    def test_plot_interactive(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            doc = pe.read_enzymeml("tests/fixtures/modeling/enzmldoc_reaction.json")
            layer = ThinLayerCopasi(doc, tmp_dir)
            layer.optimize()

            out_file = "test.html"
            pe.plot_interactive(
                layer.enzmldoc,
                thinlayer=layer,
                output_nb=False,
                show=False,
                out=out_file,
            )

    def test_rate_rule(self):
        doc = pe.read_enzymeml("tests/fixtures/modeling/enzmldoc.json")

        with tempfile.TemporaryDirectory() as tmp_dir:
            layer = ThinLayerCopasi(doc, tmp_dir)
            layer.optimize()

            out_file = "test2.html"
            pe.plot_interactive(
                layer.enzmldoc,
                thinlayer=layer,
                output_nb=False,
                show=False,
                out=out_file,
            )

    @staticmethod
    def _extract_parameter(doc: v2.EnzymeMLDocument, symbol: str) -> v2.Parameter:
        param = next(p for p in doc.parameters if p.symbol == symbol)
        assert param is not None, f"{symbol} is not set"
        return param


if __name__ == "__main__":
    # test current file only
    pytest.main([__file__])
