from pyenzyme.enzymeml.core import Replicate
from pyenzyme.enzymeml.tools import EnzymeMLReader, EnzymeMLWriter
from pyenzyme.enzymeml.core.reactant import Reactant

# Define Menten equation
def menten(s, vmax, km):
    
    return ( (-1)*vmax*s ) / ( km + s )


def generateData(init_conc, vmax, km):
    
    s = init_conc
    time, data = [], []
    
    for t in range(200):
        
        s = s + menten(s, vmax, km)
        
        time.append(t)
        data.append(s)
        
    return time, data
        
if __name__ == '__main__':
    
    # Read Strenda EnzymeML
    enzmldoc = EnzymeMLReader().readFromFile('../Resources/Examples/ThinLayers/STRENDA/Generated/3IZNOK_TEST/3IZNOK_TEST.omex', omex=True)
    
    # iterate through kinetic law parameters
    kinetic_law = enzmldoc.getReaction("r0").getModel()
    
    # parse laws
    reactant_models = dict()
    for key, item in kinetic_law.getParameters().items():
        
        param_name = key.split('_')[0]
        reactant = key.split('_')[1]
        
        if reactant in reactant_models.keys():
            
            reactant_models[reactant][param_name] = item
            
        else:
            
            reactant_models[reactant] = dict()
            reactant_models[reactant][param_name] = item
            
    # replace missing protein sequence
    enzmldoc.getProtein('p0').setSequence('MAMRIRIDLPQDEIPAQWYNILPDLPEELPPPQDPTGKSLELLKEVLPSKVLELEFAKERYVKIPDEVLERYLQVGRPTPIIRAKRLEEYLGNNIKIYLKMESYTYTGSHKINSALAHVYYAKLDNAKFVTTETGAGQWGSSVALASALFRMKAHIFMVRTSYYAKPYRKYMMQMYGAEVHPSPSDLTEFGRQLLAKDSNHPGSLGIAISDAVEYAHKNGGKYVVGSVVNSDIMFKTIAGMEAKKQMELIGEDPDYIIGVVGGGSNYAALAYPFLGDELRSGKVRRKYIASGSSEVPKMTKGVYKYDYPDTAKLLPMLKMYTIGSDFVPPPVYAGGLRYHGVAPTLSLLISKGIVQARDYSQEESFKWAKLFSELEGYIPAPETSHALPILAEIAEEAKKSGERKTVLVSFSGHGLLDLGNYASVLFKEKLAAALEHHHHHH')
            
    # add missing product
    product = Reactant("L-Tryptophan", "v0", 0.00, "mmole / l", False)
    product.setInchi("InChI=1S/C11H12N2O2/c12-9(11(14)15)5-7-6-13-10-4-2-1-3-8(7)10/h1-4,6,9,13H,5,12H2,(H,14,15)/t9-/m1/s1")
    product.setSmiles("C1=CC=C2C(=C1)C(=CN2)CC(C(=O)O)N")
    product_id = enzmldoc.addReactant(product)
    
    coproduct = Reactant("HPO4(2-)", "v0", 0.00, "mmole / l", False)
    coproduct.setInchi("InChI=1S/H3O4P/c1-5(2,3)4/h(H3,1,2,3,4)/p-2")
    coproduct.setSmiles("OP(=O)([O-])[O-]")
    coproduct_id = enzmldoc.addReactant(coproduct)
    
    enzmldoc.getReaction("r0").addProduct( product_id, 1.0, False, enzmldoc)
    enzmldoc.getReaction("r0").addProduct( coproduct_id, 1.0, False, enzmldoc)
    
    # create replicates
    repl_index = 0
    for reac_id, km in reactant_models.items():
        
        for reactant_id in enzmldoc.getReactantDict(): 
            
            if reac_id in reactant_id:
                
                init_concs = enzmldoc.getReaction('r0').getEduct(reac_id)[4]
                reactant = enzmldoc.getReactant(reac_id)
                
                for init_conc in init_concs:
                
                    kcat = reactant_models[reac_id]['kcat'][0]
                    protein_conc = enzmldoc.getProtein("p0").getInitConc()*1e-3 # n mol
                    vmax = protein_conc*kcat
                    km = reactant_models[reac_id]['km'][0]
                    
                    time, data =  generateData(init_conc, vmax, km)
                    
                    repl = Replicate("repl_%s" % (repl_index), reac_id, "conc", reactant.getSubstanceunits(), "s", init_conc)
                    repl.setData(data, time)
                    repl_index += 1
                    
                    enzmldoc.getReaction('r0').addReplicate(repl, enzmldoc)
        
    enzmldoc.printProteins()
    enzmldoc.printReactants()
    enzmldoc.printReactions()
        
    # Write Data to .omex file
    #print(EnzymeMLWriter().toXMLString(enzmldoc))
    EnzymeMLWriter().toFile(enzmldoc, "../Resources/Examples/ThinLayers/COPASI/")