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

def main():
    input = 'CoreConceptData.ttl'
    ccdontology = load_rdf(rdflib.Graph(),input)
    ccdontology = run_inferences(ccdontology)
    taxonomy = rdflib.Graph()
    taxonomy += ccdontology.triples( (None, RDFS.subClassOf, None) )
    taxonomy += ccdontology.triples( (None, RDF.type, OWL.Class) )
    n_triples(taxonomy)
    output = 'CoreConceptData_tax.rdf'
    taxonomy.serialize(destination=output,format = "application/rdf+xml")



if __name__ == '__main__':
    main()
