#-------------------------------------------------------------------------------
# Name:        pipeWorkFlowInput.py
# Purpose:      generates input data for workflow generator (APE) from a given OWL
#                data ontology and a tool annotation, in two versions:
#                one with the full ontology, the other one with a thinned out version.
#
# Author:      Schei008
#
# Created:     26-04-2019
# Copyright:   (c) Schei008 2019
# Licence:     <your licence>
#-------------------------------------------------------------------------------


import shallowOntology, typeCombinations, cleanWfTaxonomy, toolannotator
import rdflib


def pipe(tooldescfile = 'ToolDescription.ttl', ontologyfile = 'CoreConceptData.ttl'):
    #First generates a version of both the ontology and the tool description (_ct) that combines all input/output types to intersection classes (to deal only with single types)
    typeCombinations.combineTypes(tooldescfile, ontologyfile)
    #Then generates a taxonomy (_tax) version of the ontology as well as of the given tool hierarchy (=subClassOf), by applying reasoning and removing all other statements
    cleanWfTaxonomy.main(ontologyfile = 'CoreConceptData_ct.ttl', tooldesc='ToolDescription_ct.ttl')
    final = rdflib.Graph()
    final.parse('CoreConceptData_tax.ttl', format='turtle')
    final.parse('ToolDescription_tax.ttl', format='turtle')
    final.serialize(destination='GISTaxonomy.rdf', format = "application/rdf+xml")
    #Then generates a JSON version of the tooldescription for the full taxonomy (to be used with GISTaxonomy.rdf)
    toolannotator.main(toolsinrdf= 'ToolDescription_ct.ttl')
    #Generates a flattened (_fl) ontology by removing classes that inherit classlist, then generates a corresponding flattened tooldescription, by substituting classes with the LUC in the flattened ontology
    shallowOntology.main(tooldescfile = "ToolDescription_ct.ttl", ontologyfile = 'CoreConceptData_tax.ttl', classlist = ["FieldQ", "NetworkDS", "NetworkQ", "CoreConceptDataSet", "NominalA", "EventQ", "ObjectQ", "BoundedPhen", "FieldDS", "EventDS", "ObjectDS", "AmountDS"] )
    finalfl = rdflib.Graph()
    finalfl.parse('CoreConceptData_tax_fl.ttl', format='turtle')
    finalfl.parse('ToolDescription_tax.ttl', format='turtle')
    finalfl.serialize(destination='GISTaxonomy_fl.rdf', format = "application/rdf+xml")
    #JSON version of the flattened tool description (to be used with GISTaxonomy_fl.rdf
    toolannotator.main(toolsinrdf= 'ToolDescription_ct_fl.ttl')
    # JSON version of the manual flattened tool description (to be used with
    # GISTaxonomy_fl.rdf)
    toolannotator.main(toolsinrdf= 'ToolDescription_ct_fl_manual.ttl')

def main():
    pipe()




if __name__ == '__main__':
    main()
