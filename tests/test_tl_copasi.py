import unittest
import COPASI
from pyenzyme.enzymeml.tools import EnzymeMLReader
import os

import examples.ThinLayers.TL_Copasi as TL

this_dir = os.path.abspath(os.path.dirname(__file__))
temp_dir = os.path.join(this_dir, 'tmp')
if not os.path.exists(temp_dir):
    os.mkdir(temp_dir)

example_file = os.path.join(this_dir, '..', 'examples', 'ThinLayers', 'COPASI', '3IZNOK_TEST.omex')
    

class TestTlCopasi(unittest.TestCase):

    def test_copasi_version(self):
        self.assertGreaterEqual(int(COPASI.CVersion.VERSION.getVersionDevel()), 214, "Need newer COPASI version")
    
    def test_example_file_exists(self):
        self.assertTrue(os.path.exists(example_file))
    
    def test_run_thinlayer_modelfunction(self):        
        
        TL.ThinLayerCopasi().modelEnzymeML('r0', 's1', example_file, outdir=temp_dir)

        # for now only test that file exists at the end of test, might have to modify to actually get at the data
        self.assertTrue(os.path.exists(os.path.join(temp_dir, 'Modeled_r0_s1', '3IZNOK_TEST.omex')))

    def test_parameter_estimation(self):
        # the modelEnzymeML function does not actually return the parameter values, lets us do that manualy
        enzmldoc = EnzymeMLReader().readFromFile(example_file)
        
        km_val, km_unit, vmax_val, vmax_unit = TL.ThinLayerCopasi().importEnzymeML( 'r0', 's1', temp_dir, enzmldoc )
        
        self.assertAlmostEqual(km_val, 0.01, places=3)
        self.assertAlmostEqual(vmax_val, 0.00015, places=5)

