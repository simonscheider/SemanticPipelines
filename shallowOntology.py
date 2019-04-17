#-------------------------------------------------------------------------------
# Name:        shallowOntology
# Purpose:      Remove all classes of an ontology that are subclasses of a given list of classes
#
# Author:      Schei008
#
# Created:     16-04-2019
# Copyright:   (c) Schei008 2019
# Licence:     <your licence>
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
WF = rdflib.Namespace('http://geographicknowledge.de/vocab/Workflow.rdf#')
CCD = rdflib.Namespace('http://geographicknowledge.de/vocab/CoreConceptData.rdf#')

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
    g.bind('wf', 'http://geographicknowledge.de/vocab/Workflow.rdf#')
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

def write_rdf(g, rdffile, format='turtle' ):
    g.serialize(destination=rdffile,format = format)



def recRemoveR(cl, ontology):
    ob = ontology.objects(cl,None)
    for o in ob:
        recRemoveR(o, ontology)
    ontology.remove((cl, None, None))

def recRemoveDef(cl, ontology):
    ob = ontology.objects(cl,OWL.equivalentClass)
    for o in ob:
        if o != None:
            recRemoveR(o,ontology)
    ontology.remove((cl, OWL.equivalentClass, None))

def recRemoveL(cl, ontology):
    sub = ontology.subjects(RDFS.subClassOf, cl)
    for s in sub:
        print s
        recRemoveDef(s,ontology)
        recRemoveL(s, ontology)
        ontology.remove((s, None, None))
    ontology.remove((None, RDFS.subClassOf, cl))


def flattenOntology(ontologyfile, classlist ):
    ontology =load_rdf(rdflib.Graph(),ontologyfile)
    ontology = setprefixes(ontology)
    base = 'http://geographicknowledge.de/vocab/CoreConceptData.rdf'
    classlist = [URIRef(str(base)+"#"+c) for c in classlist]
    newontfile = os.path.splitext(ontologyfile)[0]+'_fl'+os.path.splitext(ontologyfile)[1]
    for c in classlist:
            print c
            recRemoveDef(c,ontology)
            recRemoveL(c,ontology)
            ontology.remove((c, None, None))
    n_triples(ontology)
    write_rdf(ontology,newontfile)
    return newontfile



def flattenToolAnnotations(annotationfile, ontologyfile, flattenedontologyfile):
    ontology =load_rdf(rdflib.Graph(),ontologyfile)
    ontology = setprefixes(ontology)
    flattenedontology =load_rdf(rdflib.Graph(),flattenedontologyfile)
    flattenedontology = setprefixes(flattenedontology)
    anno = load_rdf(rdflib.Graph(),annotationfile)
    flattenedtools = rdflib.Graph()
    out = os.path.splitext(annotationfile)[0]+'_fl'+os.path.splitext(annotationfile)[1]
    #iterate over all tools
    wf = [WF.output, WF.input1, WF.input2, WF.input3]
    for t in anno.objects(None,TOOLS.implements):
        for p in wf:
            cl = anno.value(anno.value(t,p),  RDF.type)
            luc = getflattenedLUC(flattenedontology, ontology, cl)
            if luc != None:
                b = BNode()
                flattenedtools.add((t,p,b))
                flattenedtools.add((b,RDF.type,luc))
    flattenedtools = setprefixes(flattenedtools)
    flattenedtools.serialize(destination=out,format = "turtle")




##Gets the depth of a class in an ontology hierarchy (lattice)
def getDepth(ontology, cl, level):
    depth = level
    for super in ontology.objects(cl, RDFS.subClassOf):
        d = getDepth(ontology,super,level+1)
        depth = d if d > depth else depth
    return depth

#Get the super concept with the highest depth in the flattened ontology
def getflattenedLUC(flattenedontology, ontology, cl):
       d = 0
       luc = None
       if (cl,None,None) in flattenedontology:
            d = getDepth(flattenedontology,cl,0)
            luc = cl
       for super in ontology.objects(cl, RDFS.subClassOf):
            returndepth, lucc = getflattenedLUC(flattenedontology, ontology, super)
            if returndepth > d:
                d = returndepth
                luc = lucc
       return d, luc









def main():
    classlist = ["FieldQ", "NominalA", "EventQ", "ObjectQ"] #This is the list of classes that should get kicked out of the ontology
    ontologyfile = 'CoreConceptData_tax.ttl'
    flattenedontologyfile = flattenOntology(ontologyfile, classlist)
    #flattenToolAnnotations("ToolDescription_ct.ttl", ontologyfile, flattenedontologyfile)

    ontology =load_rdf(rdflib.Graph(),flattenedontologyfile)
    ontology = setprefixes(ontology)
    base = 'http://geographicknowledge.de/vocab/CoreConceptData.rdf'
    classlist = [URIRef(str(base)+"#"+c) for c in classlist]
    print getDepth(ontology, classlist[0],0)


if __name__ == '__main__':
    main()
