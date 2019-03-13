#-------------------------------------------------------------------------------
# Name:        Type Combinations
# Purpose:     This script takes an RDF file and an OWL ontology containing
#              OWL classes and generates new versions of both files. In this new
#              version, all types (classes that are not subclasses of each other)
#              of a given node in the RDF file are combined into a combined class
#               using class intersection (conjunction). The new class is added to
#               the ontology and the nodes in the RDF file are instantiated.
#
# Author:      Schei008
#
# Created:     13-03-2019
# Copyright:   (c) Schei008 2019
# Licence:     MIT
#-------------------------------------------------------------------------------

__author__      = "Simon Scheider"
__copyright__   = ""

import rdflib
import rdflib.plugins.sparql as sparql
import glob
import RDFClosure
from rdflib.namespace import RDFS, RDF, OWL
from rdflib import URIRef, BNode, Literal
from rdflib import Namespace
from urlparse import urlparse
import os



"""Reasoning stuff"""
def run_inferences( g ):
    print('run_inferences')
    # expand deductive closure
    RDFClosure.DeductiveClosure(RDFClosure.RDFS_Semantics).expand(g)
    #RDFClosure.DeductiveClosure(RDFClosure.OWLRL_Semantics).expand(g)
    n_triples(g)
    return g



"""Helper stuff"""
def load_rdf( g, rdffile, format='turtle' ):
    #print("load_ontologies")
        #print("  Load RDF file: "+fn)
    g.parse( rdffile, format = format )
    n_triples(g)
    return g

def n_triples( g, n=None ):
    """ Prints the number of triples in graph g """
    if n is None:
        print( '  Triples: '+str(len(g)) )
    else:
        print( '  Triples: +'+str(len(g)-n) )
    return len(g)

def printGraph(graph):
    for s, p, o in graph:
        print s, p,  o

def file_to_str(fn):
    """
    Loads the content of a text file into a string
    @return a string
    """
    with open(fn, 'r') as f:
        content=f.read()
    return content

""""checks subsumption by property path query (fast)"""
def isSubTypeOf(type1, supertype, ontology): #test if an owl class is a subclass of another inside an ontology
    q = """ASK {
          %s rdfs:subClassOf+ %s .
       }""" % (type1.n3(), supertype.n3())
    #print q
    qres = ontology.query( q )
    if qres:
        return True
    else:
        return False

""""Cleans list of types to contain only classes that are not superclasses of each other"""
def cleanTypes(types, expontology):
    cleanedtypes = [] #Types that are not subclasses of each other
    for t in types:
            add = True
            for tt in types:
                if t != tt:
                    if isSubTypeOf(tt,t,expontology):
                        add=False
            if add: #If t is no supertype of any other type
                cleanedtypes.append(t)
    return cleanedtypes

def orderTypes(types):
    return sorted(types)

#Generates a new class that is the intersection of classes and inserts it into the given graph
def intersectTypes(types, base, cg):
    newclass = URIRef(str(base)+"#"+"".join([str(t).split("#")[-1] for t in types]))
    print newclass
    cg.add((newclass, RDF.type, OWL.Class))
    b = BNode()
    cg.add((newclass, OWL.equivalentClass, b))

    listName = BNode()
    cg.add((b, OWL.intersectionOf, listName))
    prevlist= listName
    for idx,t in enumerate(types): #Creates an RDF Collection of types
        if idx +1 == len(types):
            listItem = RDF.nil
        else:
            listItem = BNode()
        cg.add((prevlist, RDF.first, t))
        cg.add((prevlist, RDF.rest, listItem))
        prevlist =listItem
    return cg





def combineTypes(rdffile, ontology):
    rdfdata =load_rdf(rdflib.Graph(),rdffile)
    ontdata =load_rdf(rdflib.Graph(),ontology)
    #expontology = run_inferences(ontology)
    base = [s for s in ontdata.subjects(RDF.type, OWL.Ontology)][0]

    for s,p,o in rdfdata.triples((None, RDF.type, None)): #Iterate over typed nodes in the RDF file
        types = [otype for otype in rdfdata.objects(s, RDF.type)] #Get all classes of this node
        print types
        cleanedtypes = cleanTypes(types,ontdata)
        print cleanedtypes
        if len(cleanedtypes)>1:
            orderedtypes = orderTypes(cleanedtypes)
            print orderedtypes
            newontologydata = intersectTypes(orderedtypes, base, ontdata)
            break

















def main():
    combineTypes('ToolDescription_full.ttl', 'CoreConceptData.ttl')

if __name__ == '__main__':
    main()
