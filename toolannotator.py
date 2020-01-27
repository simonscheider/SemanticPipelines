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
from urllib.parse import urlparse
import os

from xml.etree.ElementTree import Element, SubElement, Comment, tostring
from xml.etree import ElementTree
from xml.dom import minidom

import json

TOOLS=rdflib.Namespace("http://geographicknowledge.de/vocab/GISTools.rdf#")
WF= rdflib.Namespace("http://geographicknowledge.de/vocab/Workflow.rdf#")

# def prettify(elem):
#     """Return a pretty-printed XML string for the Element.
#     """
#     rough_string = ElementTree.tostring(elem, 'utf-8')
#     reparsed = minidom.parseString(rough_string)
#     return reparsed.toprettyxml(indent="  ")


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


def n_triples( g, n=None ):
    """ Prints the number of triples in graph g """
    if n is None:
        print(( '  Triples: '+str(len(g)) ))
    else:
        print(( '  Triples: +'+str(len(g)-n) ))
    return len(g)


def shortURInames(URI):
    if "#" in URI:
        return URI.split('#')[1]
    else:
        return os.path.basename(os.path.splitext(URI)[0])


def getinoutypes(g, predicate, subject):
    """Returns a list of names of types that """
    output = g.value(predicate = predicate, subject = subject, any = False)
    if not output:
        raise Exception(f'Could not find object with subject {subject} and predicate {predicate}!')
    outputtypes = [outputtype for outputtype in g.objects(output, RDF.type)]

    return [shortURInames(t) for t in outputtypes]


def getToollistasDict(toolsinrdf= 'ToolDescription.ttl'):
    """Read the tool annotations from the TTL file, and return a string
    representation in XML format that APE understands."""
    toollist= {'functions': []}
    trdf = load_rdf(rdflib.Graph(), toolsinrdf)
    trdf = setprefixes(trdf)
    tools = [tool for tool in trdf.objects(None, TOOLS.implements)]
    for t in tools:
        inputs = []
        for p in [WF.input1, WF.input2, WF.input3]:
            if trdf.value(subject=t, predicate=p, default=None) != None:
                inputs += [{"DType": x} for x in getinoutypes(trdf, p, t)]
        
        outtypes = getinoutypes(trdf, WF.output, t)
        outputs = [{"DType": outtypes}]
        
        name = shortURInames(t)
        toolobj ={'name': name}
        toolobj['inputs']= inputs
        toolobj['outputs']= outputs
        toolobj['operation'] = name
        toollist['functions'].append(toolobj)
        print(toolobj)
    return toollist


def main(toolsinrdf= 'ToolDescription_ct.ttl'):
    """Read tool annotations from TTL file, convert it to a JSON format that
    APE understands, and write it to a file."""

    dict_form = getToollistasDict(toolsinrdf)
    outpath = os.path.splitext(toolsinrdf)[0]+".json"
    with open(outpath, 'w') as f:
        json.dump(dict_form, f, sort_keys=True, indent=2)


if __name__ == '__main__':
    main()
