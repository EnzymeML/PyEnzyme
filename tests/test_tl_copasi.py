import unittest
import COPASI
import os
import time

from pyenzyme.thinlayers.TL_Copasi import ThinLayerCopasi

this_dir = os.path.abspath(os.path.dirname(__file__))
temp_dir = os.path.join(this_dir, 'tmp')
if not os.path.exists(temp_dir):
    os.mkdir(temp_dir)
out_dir = os.path.join(this_dir, 'out')
if not os.path.exists(out_dir):
    os.mkdir(out_dir)

class TestTlCopasi(unittest.TestCase):

    example_file1 = os.path.join(this_dir, '..', 'examples', 'ThinLayers', 'COPASI', '3IZNOK_Simulated.omex')
    example_file2 = os.path.join(this_dir, '..', 'examples', 'ThinLayers', 'COPASI', 'PGM-ENO.omex')
    example_file3 = os.path.join(this_dir, '..', 'examples', 'ThinLayers', 'COPASI', 'Model_4.omex')
    init_file = os.path.join(this_dir, '..', 'examples', 'ThinLayers', 'COPASI', 'Model_4_init.yaml')

    def test_copasi_version(self):
        self.assertGreaterEqual(int(COPASI.CVersion.VERSION.getVersionDevel()), 214, "Need newer COPASI version")
    
    def test_example_file_exists(self):
        self.assertTrue(os.path.exists(self.example_file1))
        self.assertTrue(os.path.exists(self.example_file2))
        self.assertTrue(os.path.exists(self.example_file3))
        self.assertTrue(os.path.exists(self.init_file))
    
    # def test_example_3IZNOK_Simulated(self):
    #     thin_layer = ThinLayerCopasi(path=self.example_file1, outdir=temp_dir)
    #     self.assertEqual(thin_layer.reaction_data['r0'][0].parameters[0].name, 'k_cat')
    #     self.assertEqual(thin_layer.reaction_data['r0'][0].parameters[0].value, 0.015)
    #     self.assertEqual(thin_layer.reaction_data['r0'][0].parameters[1].name, 'k_m')
    #     self.assertEqual(thin_layer.reaction_data['r0'][0].parameters[1].value, 0.01)
    #     thin_layer.task.setMethodType(COPASI.CTaskEnum.Method_Statistics)
    #     thin_layer.optimize()
    #     new_doc = thin_layer.write()
    #     del thin_layer
    #
    # def test_example_ENO(self):
    #     thin_layer = ThinLayerCopasi(path=self.example_file2, outdir=temp_dir)
    #     fit_items = thin_layer.get_fit_parameters()
    #     initial_values = [val['start'] for val in fit_items]
    #     result = thin_layer.optimize().reset_index().to_dict(orient='records')
    #     new_values = [val['value'] for val in result]
    #     self.assertNotEqual(initial_values, new_values)
    #     del thin_layer

    def test_example_Model4(self):
        print('start test', flush=True)
        start = time.perf_counter_ns()
        self.thin_layer = ThinLayerCopasi(path=self.example_file3, outdir=temp_dir, init_file=self.init_file)
        duration = time.perf_counter_ns() - start
        print(f"initialize tl:  {duration // 1000000}ms.", flush=True)
        start = time.perf_counter_ns()
        self.thin_layer.enzmldoc.toFile(out_dir, 'test', flush=True)
        duration = time.perf_counter_ns() - start
        print(f"write file:  {duration // 1000000}ms.", flush=True)
        start = time.perf_counter_ns()
        fit_items = self.thin_layer.get_fit_parameters()
        initial_values = [val['start'] for val in fit_items]
        duration = time.perf_counter_ns() - start
        print(f"get fit paramters:  {duration // 1000000}ms.", flush=True)
        start = time.perf_counter_ns()
        self.thin_layer.task.setMethodType(COPASI.CTaskEnum.Method_Statistics)
        self.thin_layer.optimize()
        duration = time.perf_counter_ns() - start
        print(f"optimize:  {duration // 1000000}ms.", flush=True)
        start = time.perf_counter_ns()
        new_values = [val for val in self.thin_layer.problem.getSolutionVariables()]
        self.assertNotEqual(initial_values, new_values)
        duration = time.perf_counter_ns() - start
        print(f"get result:  {duration // 1000000}ms.", flush=True)
        start = time.perf_counter_ns()
        new_doc = self.thin_layer.write()
        duration = time.perf_counter_ns() - start
        print(f"create new document:  {duration // 1000000}ms.", flush=True)
        start = time.perf_counter_ns()
        new_doc.toFile(out_dir, 'test2')
        duration = time.perf_counter_ns() - start
        print(f"write document:  {duration // 1000000}ms.", flush=True)
        self.assertIsNotNone(new_doc)
