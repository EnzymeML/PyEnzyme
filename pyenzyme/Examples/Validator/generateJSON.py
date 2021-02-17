import pandas as pd
import numpy as np
import json
import argparse

def generateValidField( type_, importance, val_range=None, vocab=None ):
    
    if vocab:
        # Vocab check
        if type(vocab) != list: vocab = [vocab]
        
        for voc in vocab:
            # Check if vocabulary is string
            if type(voc) != str:
                raise TypeError("Vocab element has to be string!")
    
    if val_range:  
        # val_range check
        if type(val_range) != list:
            raise TypeError("val_range has to be provided as list")
        if len(val_range) != 2:
            raise AttributeError("val_range hast to include minimum and maximum exclusively")
    
    # check types via dirctionary
    type_dict = { "str": str, "int": int, "float": float, "bool": bool }
    
    # generate dicionary
    valid_template = dict()
    valid_template["importance"] = importance
    
    if type_ in type_dict.keys():
        valid_template["type"] = type_
    
    if val_range: 
        if type_ == "int" or type_ == "float": 
            valid_template["val_range"] = [val_range[0], val_range[1]]
    
    elif vocab: valid_template["vocab"] = vocab
          
    return valid_template

def composeValidationTemplate( 
                              fname,
                              enzmldoc=None, 
                              creator=None, 
                              reaction=None, 
                              protein=None, 
                              reactant=None,
                              replicate=None,
                              vessel=None,
                              model=None,
                              ):
    
    valid_temp = dict()
    
    if enzmldoc: valid_temp["EnzymeMLDocument"] = enzmldoc
    if creator: valid_temp["Creator"] = creator
    if reaction: valid_temp["EnzymeReaction"] = reaction
    if protein: valid_temp["Protein"] = protein
    if reactant: valid_temp["Reactant"] = reaction
    if replicate: valid_temp["Replicate"] = replicate
    if vessel: valid_temp["Vessel"] = vessel
    if model: valid_temp["model"] = model
    
    with open('%s.json' % fname.split('.')[0], 'w') as f:
        json.dump( valid_temp, f, sort_keys=True, indent=4 )
    
    return 'JSON file has been written to ' + '%s.json' % fname.split('.')[0]

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='Converts a EnzymeML Validator spreadsheet to a RESTful-compatible JSOn representation.')
    parser.add_argument('-p', type=str, help='Path to spreadsheet template')
    args = parser.parse_args()
    name = args.p
    
    df = pd.read_excel(name, skiprows=2)
    classes = list( set( df.clss ) )
    
    params = dict()
    params['fname'] = name
    
    # Parse into fields 
    for clss in classes:
        
        df_red = df[ df.clss == clss ]
        df_red = df_red.replace(np.nan, 'nan', regex=True)
        fields = dict()
        
        for index, row in df_red.iterrows():
            
            att_name = row['atts']
            att_type = row['Data Type']

            if row['Range'] != 'nan':

                val_max = row['Range'].split('-')[1]
                val_min = row['Range'].split('-')[0]
                val_range = [ float(val_min), float(val_max) ]
                
            elif row['Range'] == 'nan': 
                val_range = None
                
            if row['Vocabulary'] != 'nan':
                
                vocab = row['Vocabulary'].split(',')
                
            elif row['Vocabulary'] == 'nan': 
                vocab = None
            
            # Create Field for JSON valid file
            importance = row['Attribute Importance']
            fields[att_name] = generateValidField(att_type, importance, val_range, vocab)
            
        params[clss] = fields
        
    # compose everything
    print("\n", composeValidationTemplate(**params), '\n')