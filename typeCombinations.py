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
from rdflib.namespace import RDFS, RDF, OWL
from rdflib import URIRef, BNode, Literal
from rdflib import Namespace
from urllib.parse import urlparse
import os

CCD= rdflib.Namespace("http://geographicknowledge.de/vocab/CoreConceptData.rdf#")

"""Helper stuff"""
def load_rdf( g, rdffile, format='turtle' ):
    #print("load_ontologies")
        #print("  Load RDF file: "+fn)
    g.parse( rdffile, format = format )
    n_triples(g)
    return g

def write_rdf(g, rdffile, format='turtle' ):
    g.serialize(destination=rdffile,format = format)

def n_triples( g, n=None ):
    """ Prints the number of triples in graph g """
    if n is None:
        print(( '  Triples: '+str(len(g)) ))
    else:
        print(( '  Triples: +'+str(len(g)-n) ))
    return len(g)

def printGraph(graph):
    for s, p, o in graph:
        print(s, p,  o)


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

def checkClassInter(ontology, types): #Checks whether an intersection of the given types already exists in the ontology and if yes, retrieves it
    q0 = """SELECT ?class WHERE {
           ?class owl:equivalentClass  / owl:intersectionOf ?b. """
    var = 'b'
    filters = ''
    typelist = '('+' , '.join(["<"+str(t)+">" for t in types])+')'
    for idx,t in enumerate(types):
        t = str(t)
        if idx+1 == len(types):
            rest = "rdf:nil"
        else:
            rest = '?'+var+'r'
        q0 +=""" ?%s rdf:first ?%s; rdf:rest %s .""" % (var, t.split('#')[1], rest)
        filters += """ FILTER (?%s IN """ % (t.split('#')[1]) + typelist+""") """
        var =var+'r'
    q = q0 + filters + "}"
    #print q
    qres = ontology.query( q )
    if qres:
        for res in qres:
            return res[0]
            break
    else:
        return None

#Generates a new class that is the intersection of classes and inserts it into the given graph
def intersectTypes(types, base, cg):
    newclass = URIRef(str(base)+"#"+"".join([str(t).split("#")[-1] for t in types]))
    check = checkClassInter(cg, types)
    if check == None : #only update if class does not exist yet
        #print 'New type: '+str(newclass)
        cg.add((newclass, RDF.type, OWL.Class))
        b = BNode()
        cg.add((newclass, OWL.equivalentClass, b))
        listName = BNode()
        cg.add((b, OWL.intersectionOf, listName))
        prevlist= listName
        for idx,t in enumerate(types): #Creates an RDF Collection of types as a class intersection. Also adds explicit subclass statements
            cg.add((newclass, RDFS.subClassOf, t))
            if idx +1 == len(types):
                listItem = RDF.nil
            else:
                listItem = BNode()
            cg.add((prevlist, RDF.first, t))
            cg.add((prevlist, RDF.rest, listItem))
            prevlist =listItem
        return newclass
    else:
        #print 'Old type: '+str(check)
        return check


def setprefixes(g):
    g.bind('foaf', 'http://xmlns.com/foaf/0.1/')
    g.bind( 'ccd', 'http://geographicknowledge.de/vocab/CoreConceptData.rdf#')
    g.bind( 'owl', 'http://www.w3.org/2002/07/owl#')
    g.bind( 'rdf', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#')
    g.bind( 'xml', 'http://www.w3.org/XML/1998/namespace')
    g.bind( 'xsd', 'http://www.w3.org/2001/XMLSchema#')
    g.bind( 'rdfs', 'http://www.w3.org/2000/01/rdf-schema#')
    g.bind('em', 'http://geographicknowledge.de/vocab/ExtensiveMeasures.rdf#')
    g.bind('ada', 'http://geographicknowledge.de/vocab/AnalysisData.rdf#')
    return g


def combineTypes(rdffile, ontology, singletype = True): #singltype: should the resulting nodes in the rdffile have only a single type?
    rdfdata =load_rdf(rdflib.Graph(),rdffile)
    rdfdata = setprefixes(rdfdata)
    print("Intersecting types (creating new leave classes in the ontology for each new type combination occurring in a tool's input/output annotation)")

    ontdata =load_rdf(rdflib.Graph(),ontology)
    ontdata = setprefixes(ontdata)
    newontfile = os.path.splitext(ontology)[0]+'_ct'+os.path.splitext(ontology)[1]
    newrdffile =os.path.splitext(rdffile)[0]+'_ct'+os.path.splitext(rdffile)[1]

    base = [s for s in ontdata.subjects(RDF.type, OWL.Ontology)][0]
    subjects =  list(set(rdfdata.subjects(RDF.type, None)))
    ttypes = [[otype for otype in rdfdata.objects(s, RDF.type)] for s in subjects] #Get all classes of this node
    for idx,s in enumerate(subjects): #Iterate over typed nodes in the RDF file
        types = ttypes[idx]
        #print types
        cleanedtypes = cleanTypes(types,ontdata)
        #print cleanedtypes
        if len(cleanedtypes)>1:
            orderedtypes = orderTypes(cleanedtypes)
            #print orderedtypes
            newclass = intersectTypes(orderedtypes, base, ontdata)
            if singletype: #If yes, remove the old type statements
                rdfdata.remove( (s, RDF.type, None) )
            rdfdata.add( (s, RDF.type, newclass) )
    write_rdf(ontdata,newontfile)
    write_rdf(rdfdata,newrdffile)



















def main():
    combineTypes('ToolDescription.ttl', 'CoreConceptData.ttl')



if __name__ == '__main__':
    main()
