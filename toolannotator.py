#-------------------------------------------------------------------------------
# Name:        Tool Annotator
# Purpose:      Takes an RDF based specification of tools with typed inputs and outputs
#               turns it into an tool description in XML according to the APE format
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

from rdflib.namespace import RDFS, RDF, OWL
from rdflib import URIRef, BNode, Literal
from rdflib import Namespace
from urlparse import urlparse
import os

from xml.etree.ElementTree import Element, SubElement, Comment, tostring
from xml.etree import ElementTree
from xml.dom import minidom

TOOLS=rdflib.Namespace("http://geographicknowledge.de/vocab/GISTools.rdf#")
WF= rdflib.Namespace("http://geographicknowledge.de/vocab/Workflow.rdf#")

def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ElementTree.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


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
    g.bind('gis', 'http://geographicknowledge.de/vocab/GISConcepts.rdf#')
    g.bind('tools', 'http://geographicknowledge.de/vocab/GISTools.rdf#')
    return g

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


def tools2XML(toollist=[{'operationname': 'spatialJoinSumTessRatio', 'inputs':[['ObjectVector','RatioA', 'ERA'], ['ObjectRegion']], 'outputs':[['Lattice', 'RatioA', 'ERA']]}]):
    top = Element("functions")
    comment = Comment('Contains all typed ArcGIS Pro tools for workflow analysis')
    top.append(comment)
    for t in toollist:
        function = SubElement(top, 'function')
        function.set('name',t['operationname']) #operationname
        operation = SubElement(function, 'operation')
        operation.text =t['operationname']
        inputs = SubElement(function, 'inputs')
        for i in t['inputs']:
            input = SubElement(inputs, 'input')
            for it in i:
                inputtype =SubElement(input, 'type')
                inputtype.text =it
        outputs = SubElement(function, 'outputs')
        for o in t['outputs']:
            output = SubElement(outputs, 'output')
            for ot in o:
                outputtype =SubElement(output, 'type')
                outputtype.text =ot
        implementation = SubElement(function, 'implementation')
        code = SubElement(implementation, 'code')
        code.text = t['operationname']
    return top


def shortURInames(URI):
    return URI.split('#')[1]

def getinoutypes(g, predicate, subject):
        output = g.value(predicate = predicate, subject = subject, any = False)
        outputtypes = [outputtype for outputtype in g.objects(output, RDF.type)]
        return [shortURInames(t) for t in outputtypes]


def getToollistasXML(toolsinrdf= 'ToolDescription.ttl'):
    toollist= []
    trdf = load_rdf(rdflib.Graph(),toolsinrdf)
    trdf =setprefixes(trdf)
    tools = [tool for tool in trdf.objects(None, TOOLS.implements)]
    for t in tools:
        print t
        toolobj ={'operationname':shortURInames(t)}
        inputs = []
        for p in [WF.input1, WF.input2, WF.input3]:
            if trdf.value(subject = t, predicate = p,default=None) != None:
                inputs.append(getinoutypes(trdf, p,t))
        outputs = []
        outputs.append(getinoutypes(trdf, WF.output,t)) #trdf.value(predicate = WF.output, subject = t, any = False)
        #print inputs
        #print outputs
        toolobj['inputs']= inputs
        toolobj['outputs']= outputs
        toollist.append(toolobj)
        print toolobj
    return prettify(tools2XML(toollist))






def main(toolsinrdf= 'ToolDescription_ct.ttl'):
    #top = tools2XML()
    #print prettify(top)
    xml= getToollistasXML(toolsinrdf)
    outpath = os.path.splitext(toolsinrdf)[0]+".xml"
    print outpath
    outfile = open(outpath, "w")
    outfile.write(xml)
    #print shortURInames("http://geographicknowledge.de/vocab/Workflow.rdf#hallo")


if __name__ == '__main__':
    main()
