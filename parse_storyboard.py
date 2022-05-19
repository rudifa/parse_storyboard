#!python3
#
#  parse_storyboard.py v.0.1.1
#  Parse an Xcode .storyboard file and generate a graphviz diagram of view controllers and segues
#
#  Created by Rudolf Farkas on 02.05.2020
#  Copyright © 2020 Rudolf Farkas. All rights reserved.

# references
# https://www.datacamp.com/community/tutorials/python-xml-elementtree
# https://joris.kluivers.nl/blog/2014/02/10/storyboard-identifier-constants/
# https://graphviz.readthedocs.io/en/stable/index.html

import sys, os
import xml.etree.ElementTree as et
from argparse import ArgumentParser
import json
import re
from levenshtein_distance import find_nearest

class StoryboardParser(object):

    def __init__(self, filepath, plot):
        """Given a filepath to an Xcode .storyboatd file
        initialize the instance and parse the file.
        """
        self.filepath = filepath
        self.dir = re.split(r'\/', filepath)[0]
        self.plot_digraph = plot

        self.tree = et.parse(filepath)
        self.root = self.tree.getroot()

        self.controller_nodes = self.collect_controller_nodes()
        self.controller_name_dict = {node['id']: node['controller_name'] for node in self.controller_nodes}

        self.segue_edges = self.collect_segue_edges()

    ##########################

    def digraph(self):
        """
        From data collected from the input storyboard file construct a 
        graphviz dot object (textual representatation of graph of viewControllers and segues)
        and render it as .png
        """
        from graphviz import Digraph, Source

        dot = Digraph(name='storyboard')
        dot.attr("graph", ratio="0.5625")
        dot.attr('node', shape='rect', fontname = 'Helvetica', fontsize = '12')
        dot.attr('edge', fontname = 'Helvetica', fontsize = '11')

        dot.node('', self.dir, shape='none')
        dot.edge('', self.initial_vc_class_name())

        for node in self.controller_nodes:
            dot.node(node['controller_name'])

        edge_colors = {'relationship': 'black', 'push': 'black', 'presentation': 'blue', 'unwind': 'red'}

        for edge in self.segue_edges:
            edge_color = edge_colors[edge['kind']]
            dot.edge(edge['source'], edge['destination'], color=edge_color, label=edge['identifier'])

        dot.format = 'png'
        #print(dot.source)
        dot.render('graphviz-out/graphviz', view=self.plot_digraph)
        return dot.source

    ### collect data from storyboard

    def initial_vc_class_name(self):
        initial_vc_id = self.root.attrib['initialViewController']
        vc_class_name_dict = {vc_node['id']: vc_node['controller_name'] for vc_node in self.controller_nodes}
        return vc_class_name_dict.get(initial_vc_id, 'UNKNOWN')

    def collect_controller_nodes(self):
        """
        Return nodes representing viewControllers and navigationControllers
        """
        def vc_node(vc):
            return { 'id': vc.attrib['id'],
                    'controller_name': vc.attrib['customClass']}

        def navc_node(nc):
            return { 'id': nc.attrib['id'],
                    'controller_name': 'navigationController' + '-' + nc.attrib['id']}

        nodes = []
        for vc in self.root.iter('viewController'):
            nodes.append(vc_node(vc))
        for nc in self.root.iter('navigationController'):
            nodes.append(navc_node(nc))
        for tvc in self.root.iter('tableViewController'):
            nodes.append(vc_node(tvc))
        return nodes

    def collect_segue_edges(self):
        """
        Return edges representing segues
        """

        def relationship_segue_edge(controller_names, vc_name, segue):
            dest_controller_id = segue.attrib['destination']
            dest_vc_name = controller_names[dest_controller_id]
            return { 'id': segue.attrib['id'],
                    'source': vc_name,
                    'destination': dest_vc_name,
                    'identifier': 'navigation'}

        def presentation_segue_edge(controller_names, vc_name, segue):
            dest_controller_id = segue.attrib['destination']
            dest_vc_name = controller_names[dest_controller_id]
            return { 'id': segue.attrib['id'],
                    'source': vc_name,
                    'destination': dest_vc_name,
                    'identifier': segue.attrib['identifier']}

        def unwind_segue_edge(controller_names, vc_name, segue):
            identifier = segue.attrib['identifier'] # may end in 'VC'
            identifier_full = identifier.replace('VC', 'ViewController')
            dest_vc_name = find_nearest(identifier_full, controller_names)
            print('***', identifier, identifier_full, dest_vc_name)
            return { 'id': segue.attrib['id'],
                    'source': vc.attrib['customClass'],
                    'destination': dest_vc_name,
                    'identifier': identifier}

        controller_name_dict = self.controller_name_dict
        edges = []
        for vc in list(self.root.iter('viewController')) +\
                  list(self.root.iter('navigationController')) +\
                  list(self.root.iter('tableViewController')):
            vc_id = vc.attrib['id']
            vc_name = controller_name_dict[vc_id]
            for segue in vc.iter('segue'):
                edge = None
                kind = segue.attrib['kind']
                if kind == 'relationship':
                    edge = relationship_segue_edge(controller_name_dict, vc_name, segue)
                elif kind == 'presentation' or kind == 'push':
                    edge = presentation_segue_edge(controller_name_dict, vc_name, segue)
                elif kind == 'unwind':
                    edge = unwind_segue_edge(controller_name_dict.values(), vc_name, segue)
                if edge:
                    edge['kind'] = kind
                    edges.append(edge)
        return edges

    ### for preliminary investigation

    def root_info(self):
        strs = []
        #strs.append(json.dumps(self.root.tag))
        #strs.append(json.dumps(self.root.attrib))
        strs.append(self.dump(self.root.attrib, ['initialViewController']))
        return "\n".join(strs)

    def navigationControllers_info(self):
        strs = []
        for vc in self.root.iter('navigationController'):
            strs.append(json.dumps(vc.attrib))
            #strs.append(self.dump(vc.attrib, ['id']))
            for segue in vc.iter('segue'):
                strs.append('        segue ' + self.dump(segue.attrib, ['id', 'destination', 'kind', 'identifier', 'unwindAction', 'modalPresentationStyle',  'modalTransitionStyle']))
                #{"destination": "aZf-qq-fub", "kind": "presentation", "identifier": "toStickerShopVC", "modalPresentationStyle": "fullScreen", "modalTransitionStyle": "crossDissolve", "id": "Dde-ZG-iRW"}
        strs.append('')
        return "\n".join(strs)

    def viewControllers_info(self):
        strs = []
        for vc in self.root.iter('viewController'):
            strs.append(json.dumps(vc.attrib))
            #strs.append(self.dump(vc.attrib, ['id', 'customClass']))
            for segue in vc.iter('segue'):
                #     print(segue)
                strs.append('        segue ' + self.dump(segue.attrib, ['id', 'destination', 'kind', 'identifier', 'unwindAction', 'modalPresentationStyle',  'modalTransitionStyle']))
                #{"destination": "aZf-qq-fub", "kind": "presentation", "identifier": "toStickerShopVC", "modalPresentationStyle": "fullScreen", "modalTransitionStyle": "crossDissolve", "id": "Dde-ZG-iRW"}
        strs.append('')
        return "\n".join(strs)

    def segue_info(self):
        strs = ['??']
        for segue in self.root.iter("segue"):
            #strs.append(segue.tostring())
            strs.append(json.dumps(segue.attrib))
        #return "\n".join(strs)
        return ''

    def dump(self, dict, keys):
        strs = []
        for key in keys:
            if key in dict:
                strs.append(f'    {key}: {dict[key]}')
        return '  '.join(strs)

def print_detail_info(sb):

    def print_list(list_name, list):
        print(f'{list_name}:')
        for item in list:
            print(' ', item)   

    def print_dict(dict_name, dict):
        print(f'{dict_name}:')
        for key, value in dict.items():
            print(f'  {key}: {value}')   

    print('root_info:', sb.root_info())
    print_list('controller_nodes', sb.controller_nodes)
    print_dict('controller_name_dict', sb.controller_name_dict)
    print_list('segue_edges', sb.segue_edges)

if __name__ == "__main__":
    parser = ArgumentParser(description='Analyzes an Xcode .storyboard file and generates a graphviz digraph and a plot of view controllers and segues')
    parser.add_argument("filepath", type=str, default=None, help='an Xcode .storyboard file')
    parser.add_argument('--no-plot', dest='plot', action='store_false', help='suppress the on-screen plot')
    parser.set_defaults(plot=True)
    args = parser.parse_args()
    print("args.filepath=", args.filepath)

    sb = StoryboardParser(args.filepath, args.plot)
    print_detail_info(sb)
    sbd = sb.digraph()
    print(sbd)


