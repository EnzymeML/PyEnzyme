import unittest
import COPASI
import os

from pyenzyme.thinlayers import ThinLayerCopasi

this_dir = os.path.abspath(os.path.dirname(__file__))
temp_dir = os.path.join(this_dir, 'tmp')
if not os.path.exists(temp_dir):
    os.mkdir(temp_dir)

example_file = os.path.join(this_dir, '..', 'examples', 'ThinLayers', 'COPASI', '3IZNOK_SIMULATED.omex')
    

class TestTlCopasi(unittest.TestCase):

    def test_copasi_version(self):
        self.assertGreaterEqual(int(COPASI.CVersion.VERSION.getVersionDevel()), 214, "Need newer COPASI version")
    
    def test_example_file_exists(self):
        self.assertTrue(os.path.exists(example_file))
    
    def test_example(self):
        thin_layer = ThinLayerCopasi(path=example_file, outdir=temp_dir)
        self.assertEqual(thin_layer.reaction_data['r0'][0].parameters[0].name, 'k_cat')
        self.assertEqual(thin_layer.reaction_data['r0'][0].parameters[0].value, 0.015)
        self.assertEqual(thin_layer.reaction_data['r0'][0].parameters[1].name, 'k_m')
        self.assertEqual(thin_layer.reaction_data['r0'][0].parameters[1].value, 0.01)
        thin_layer.optimize()
        thin_layer.update_enzymeml_doc()
        self.assertEqual(thin_layer.reaction_data['r0'][0].parameters[0].name, 'k_cat')
        self.assertNotEqual(thin_layer.reaction_data['r0'][0].parameters[0].value, 0.015)
        self.assertEqual(thin_layer.reaction_data['r0'][0].parameters[1].name, 'k_m')
        self.assertNotEqual(thin_layer.reaction_data['r0'][0].parameters[1].value, 0.01)
