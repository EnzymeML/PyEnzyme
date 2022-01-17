# EnzymeML documents can, apart from what is demonstrated in 'CreateEnzymeML' example,
# also be created via the EnzymeML spreadsheet template. This example demonstrates
# a common workflow from an EnzymeML spreadsheet to a Dataverse entry.

# It should be noted, that the environment variables 'DATAVERSE_URL' and 'DATAVERSE_API_TOKEN'
# should be given approriately before the upload. If not, the upload cant be done.

from pyenzyme import EnzymeMLDocument

# Load the EnzymeML template to an EnzymeML document object
enzmldoc = EnzymeMLDocument.fromTemplate(
    "./EnzymeML_Template_Example.xlsm")
enzmldoc.toFile(".")

# Now upload the EnzymeML document to your Dataverse of choice
# enzmldoc.uploadToDataverse("dataverse_name")
