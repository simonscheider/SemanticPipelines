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
import operator


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
    g.bind('tools', 'http://geographicknowledge.de/vocab/GISTools.rdf#')
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
    removeLoops(ontology)
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
    removeLoops(ontology)
    ontology = setprefixes(ontology)
    flattenedontology =load_rdf(rdflib.Graph(),flattenedontologyfile)
    flattenedontology = setprefixes(flattenedontology)
    anno = load_rdf(rdflib.Graph(),annotationfile)
    flattenedtools = rdflib.Graph()
    out = os.path.splitext(annotationfile)[0]+'_fl'+os.path.splitext(annotationfile)[1]
    #iterate over all tools
    wf = [WF.output, WF.input1, WF.input2, WF.input3]
    for t in anno.objects(None,TOOLS.implements):
        supertool = [st for st in anno.subjects(TOOLS.implements,t)][0]
        if supertool not in flattenedtools.objects(None, TOOLS.implements):
            for p in wf:
                cl = anno.value(anno.value(t,p),  RDF.type)
                if cl is not None:
                    luc = getflattenedLUC(flattenedontology, ontology, cl)
                    b = BNode()
                    flattenedtools.add((supertool,p,b))
                    flattenedtools.add((b,RDF.type,luc))
            flattenedtools.add((TOOLS.tool ,TOOLS.implements,supertool))
    flattenedtools = setprefixes(flattenedtools)
    flattenedtools.serialize(destination=out,format = "turtle")


def removeLoops(ontology):
    removedcl = []
    for s in ontology.subjects( RDFS.subClassOf, None):
        if s not in removedcl:
            for o in ontology.objects(s, RDFS.subClassOf):
                if (o, RDFS.subClassOf, s) in ontology:
                    tt = [t for t in ontology.triples((o, RDFS.subClassOf,None))]
                    for t in tt:
                        if t[2] != s:
                            ontology.add((s, t[1], t[2]))
                    tt = [t for t in ontology.triples((None, RDFS.subClassOf,o))]
                    for t in tt:
                        if t[0] != s:
                            ontology.add((t[0], t[1], s))
                    ontology.remove((o, None, None))
                    ontology.remove((None, None, o))
                    removedcl.append(o)





##Gets the depth of a class in an ontology hierarchy (lattice) (this only works in taxonomies without loops (equivalent classes)
def getDepth(ontology, cl, level):
    depth = level
    #print "depth for :" +str(cl)
    for super in ontology.objects(cl, RDFS.subClassOf):
        d = getDepth(ontology,super,level+1)
        depth = d if d > depth else depth
    return depth


def getsuperclasses(cl, taxonomy):
    out = []
    candidates = [c for c in  taxonomy.objects(cl, RDFS.subClassOf)]
    while candidates:
        c = candidates.pop()
        if c not in out:
            out += [c]
            candidates += [i for i in taxonomy.objects(c, RDFS.subClassOf)]
    return out




#Get the super concept with the highest depth in the flattened ontology
def getflattenedLUC(flattenedontology, ontology, cl):
       d = 0
       lucs = {}
       #print "superclasses for: "+str(cl)
       supercl = list(set(getsuperclasses(cl,ontology)))
       #print supercl
       superclfl= [s for s in supercl if ((s,None,None) in flattenedontology or (None,None,s) in flattenedontology)]
       #print "flat superclasses for: "+str(cl)
       lucs = {key:getDepth(flattenedontology,key,0) for key in superclfl}
       #print lucs
       return max(lucs.iteritems(), key=operator.itemgetter(1))[0]










def main(tooldescfile = "ToolDescription_ct.ttl", ontologyfile = 'CoreConceptData_tax.ttl', classlist = ["FieldQ", "NominalA", "EventQ", "ObjectQ", "BoundedPhen"] ):
     #This is the list of classes that should get kicked out of the ontology Unions????

    flattenedontologyfile = flattenOntology(ontologyfile, classlist)
    #ontology =load_rdf(rdflib.Graph(),ontologyfile)
    #flattenedontology =load_rdf(rdflib.Graph(),flattenedontologyfile)



    #flattenedontology =load_rdf(rdflib.Graph(),flattenedontologyfile)
    #flattenedontology = setprefixes(flattenedontology)
    #base = 'http://geographicknowledge.de/vocab/CoreConceptData.rdf#'
    #classlist = [URIRef(str(base)+"#"+c) for c in classlist]
    #print getDepth(ontology, URIRef(base+"Raster"),0)

    flattenToolAnnotations(tooldescfile, ontologyfile, flattenedontologyfile)

if __name__ == '__main__':
    main()
