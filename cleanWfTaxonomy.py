#-------------------------------------------------------------------------------
# Name:        clean Workflow Taxonomy
# Purpose:      Takes an OWL 2 ontology and adds subClassOf triples by materializing
#               OWL 2 RL inferences. Removes other triples. Used as input for workflow
#               reasoning.
#
# Author:      Schei008
#
# Created:     22-03-2019
# Copyright:   (c) Schei008 2019
# Licence:     MIT
#-------------------------------------------------------------------------------
import rdflib
import rdflib.plugins.sparql as sparql
import glob
import RDFClosure
from rdflib.namespace import RDFS, RDF, OWL
from rdflib import URIRef, BNode, Literal
from rdflib import Namespace
from urlparse import urlparse
import os

TOOLS=rdflib.Namespace("http://geographicknowledge.de/vocab/GISTools.rdf#")
ADA = rdflib.Namespace("http://geographicknowledge.de/vocab/AnalysisData.rdf#")

"""Helper stuff"""
def load_rdf( g, rdffile, format='turtle' ):
    #print("load_ontologies")
        #print("  Load RDF file: "+fn)
    g.parse( rdffile, format = format )
    n_triples(g)
    return g

"""Reasoning stuff"""
def run_inferences( g ):
    #print('run_inferences')
    # expand deductive closure
    RDFClosure.DeductiveClosure(RDFClosure.OWLRL_Semantics).expand(g)
    RDFClosure.DeductiveClosure(RDFClosure.RDFS_Semantics).expand(g)
    n_triples(g)
    return g

def n_triples( g, n=None ):
    """ Prints the number of triples in graph g """
    if n is None:
        print( '  Triples: '+str(len(g)) )
    else:
        print( '  Triples: +'+str(len(g)-n) )
    return len(g)

def cleanOWLOntology(input = 'CoreConceptData_ct.ttl'): #This takes the combined types version as input
    print 'Clean OWL ontology!'
    ccdontology = load_rdf(rdflib.Graph(),input)
    print 'Running inferences:'
    ccdontology = run_inferences(ccdontology)
    taxonomy = rdflib.Graph()
    print 'Extracting subClassOf triples:'
    taxonomy += ccdontology.triples( (None, RDFS.subClassOf, None) ) #Keeping only subClassOf statements and classes
    taxonomy += ccdontology.triples( (None, RDF.type, OWL.Class) )
    n_triples(taxonomy)
    print 'Cleaning blank node triples and loops:'
    taxonomyclean = rdflib.Graph()
    for (s,p,o) in taxonomy: #Removing triples that stem from blanknodes as well as loops
        if type(s) != BNode and type(o) != BNode:
            if s != o and  s!= OWL.Nothing:
                taxonomyclean.add((s,p,o))
    n_triples(taxonomyclean)
    #add common upper class for all data types, including spatial attributes and spatial data sets
    taxonomyclean.add((ADA.ValueList,RDFS.subClassOf,TOOLS.DType))
    taxonomyclean.add((ADA.SpatialDataSet,RDFS.subClassOf,TOOLS.DType))
    return taxonomyclean

def extractToolOntology(tooldesc='ToolDescription_ct.ttl'):
    print 'Extract Tool ontology!'
    output = rdflib.Graph()
    tools = load_rdf(rdflib.Graph(),tooldesc)
    for (s,p,o) in tools.triples((None, TOOLS.implements, None)):
        output.add((o,RDFS.subClassOf,s))
        output.add((s, RDF.type, OWL.Class))
        output.add((o, RDF.type, OWL.Class))
        #add common upper class for all tool types
        output.add((s,RDFS.subClassOf,TOOLS.Tool))
    n_triples(output)
    return output


def main():
    dt = 'CoreConceptData_tax.ttl'
    tax = cleanOWLOntology()
    tooltax =extractToolOntology()
    tax.serialize(destination=dt,format = "turtle")
    to = 'ToolDescription_tax.ttl'
    tooltax.serialize(destination=to,format = "turtle")
    final = rdflib.Graph()
    final.parse(dt, format='turtle')
    final.parse(to, format='turtle')
    final.serialize(destination='GISTaxonomy.rdf', format = "application/rdf+xml")






if __name__ == '__main__':
    main()
