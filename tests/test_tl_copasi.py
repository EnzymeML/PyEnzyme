import unittest
import COPASI
import os

from pyenzyme.thinlayers import ThinLayerCopasi

this_dir = os.path.abspath(os.path.dirname(__file__))
temp_dir = os.path.join(this_dir, 'tmp')
if not os.path.exists(temp_dir):
    os.mkdir(temp_dir)


class TestTlCopasi(unittest.TestCase):

    example_file = os.path.join(this_dir, '..', 'examples', 'ThinLayers', 'COPASI', '3IZNOK_Simulated.omex')

    def test_copasi_version(self):
        self.assertGreaterEqual(int(COPASI.CVersion.VERSION.getVersionDevel()), 214, "Need newer COPASI version")
    
    def test_example_file_exists(self):
        self.assertTrue(os.path.exists(self.example_file))
    
    def test_example(self):
        thin_layer = ThinLayerCopasi(path=self.example_file, outdir=temp_dir)
        self.assertEqual(thin_layer.reaction_data['r0'][0].parameters[0].name, 'k_cat')
        self.assertEqual(thin_layer.reaction_data['r0'][0].parameters[0].value, 0.015)
        self.assertEqual(thin_layer.reaction_data['r0'][0].parameters[1].name, 'k_m')
        self.assertEqual(thin_layer.reaction_data['r0'][0].parameters[1].value, 0.01)
        thin_layer.optimize()
        new_doc = thin_layer.write()


class TestTlCopasiENO(unittest.TestCase):
    example_file = os.path.join(this_dir, '..', 'examples', 'ThinLayers', 'COPASI', 'PGM-ENO.omex')

    def test_copasi_version(self):
        self.assertGreaterEqual(int(COPASI.CVersion.VERSION.getVersionDevel()), 214, "Need newer COPASI version")

    def test_example_file_exists(self):
        self.assertTrue(os.path.exists(self.example_file))

    def test_example(self):
        thin_layer = ThinLayerCopasi(path=self.example_file, outdir=temp_dir)
        fit_items = thin_layer.get_fit_parameters()
        initial_values = [val['start'] for val in fit_items]
        result = thin_layer.optimize().reset_index().to_dict(orient='records')
        new_values = [val['value'] for val in result]
        self.assertNotEqual(initial_values, new_values)


class TestModel4(unittest.TestCase):
    example_file = os.path.join(this_dir, '..', 'examples', 'ThinLayers', 'COPASI', 'Model_4.omex')
    init_file = os.path.join(this_dir, '..', 'examples', 'ThinLayers', 'COPASI', 'Model_4_init.yaml')

    def test_copasi_version(self):
        self.assertGreaterEqual(int(COPASI.CVersion.VERSION.getVersionDevel()), 214, "Need newer COPASI version")

    def test_example_file_exists(self):
        self.assertTrue(os.path.exists(self.example_file))
        self.assertTrue(os.path.exists(self.init_file))

    def test_example(self):
        thin_layer = ThinLayerCopasi(path=self.example_file, outdir=temp_dir, init_file=self.init_file)
        thin_layer.enzmldoc.toFile('test')
        fit_items = thin_layer.get_fit_parameters()
        initial_values = [val['start'] for val in fit_items]
        thin_layer.task.setMethodType(COPASI.CTaskEnum.Method_LevenbergMarquardt)
        thin_layer.optimize()
        new_values = [val for val in thin_layer.problem.getSolutionVariables()]
        self.assertNotEqual(initial_values, new_values)
        new_doc = thin_layer.write()
        new_doc.toFile('Test')
        self.assertIsNotNone(new_doc)
