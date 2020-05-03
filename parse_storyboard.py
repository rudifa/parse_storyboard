#!/usr/bin/env python

# https://www.datacamp.com/community/tutorials/python-xml-elementtree
# https://joris.kluivers.nl/blog/2014/02/10/storyboard-identifier-constants/

import sys, os
import xml.etree.ElementTree as et
from argparse import ArgumentParser
import json
import re
from levenshtein_distance import find_nearest

class StoryboardParser(object):

    def __init__(self, filepath):
        """Given a filepath to an Xcode .storyboatd file
        initialize the instance parsing the file.
        """
        self.filepath = filepath
        self.dir = re.split(r'\/', filepath)[0]

        self.tree = et.parse(filepath)
        self.root = self.tree.getroot()

        self.vc_nodes = self.collect_vc_nodes()
        self.vc_nodes += self.collect_navc_nodes()
        self.segue_edges = self.collect_segue_edges()
        self.unwind_edges = self.collect_unwind_edges()

        # TODO 
        # regroup navigationControllers and viewControllers in controller_nodes
        # regroup relationship, presentation and navigation segues in segue_edges

    ##########################

    def digraph(self):
        from graphviz import Digraph, Source
        # https://graphviz.readthedocs.io/en/stable/api.html

        dot = Digraph(name='storyboard')
        dot.attr('node', shape='rect', fontname = 'courier', fontsize = '12')
        dot.attr('edge', fontname = 'courier', fontsize = '10')

        dot.node('', self.dir, shape='none')
        dot.edge('', self.initial_vc_class_name())

        for node in self.vc_nodes:
            dot.node(node['viewController'])

        for edge in self.segue_edges:
            dot.edge(edge['source'], edge['destination'], color='blue', label=edge['identifier'])

        for edge in self.unwind_edges:
            dot.edge(edge['source'], edge['destination'], color='red', label=edge['identifier'])

        dot.format = 'png'
        #print(dot.source)
        dot.render('graphviz-out/graphviz', view=True)
        return dot.source

    def collect_vc_nodes(self):
        """
        Return nodes representing view controllers
        """
        nodes = []
        for vc in self.root.iter('viewController'):
            nodes.append(self.vc_node(vc))
        return nodes

    def vc_node(self, vc):
        node = { 'id': vc.attrib['id'],
                'viewController': vc.attrib['customClass']
        }
        return node

    def collect_navc_nodes(self):
        """
        Return nodes representing navigation controllers
        """
        nodes = []
        for vc in self.root.iter('navigationController'):
            nodes.append(self.navc_node(vc))
        return nodes

    def navc_node(self, vc):
        node = { 'id': vc.attrib['id'],
                'viewController': 'navigationController' + '-' + vc.attrib['id']
        }
        return node

    def initial_vc_class_name(self):
        initial_vc_id = self.root.attrib['initialViewController']
        vc_class_name_dict = {vc_node['id']: vc_node['viewController'] for vc_node in self.vc_nodes}
        return vc_class_name_dict.get(initial_vc_id, 'UNKNOWN')

    def collect_segue_edges(self):
        """
        Return edges representing segues
        """
        vc_class_name_dict = {vc_node['id']: vc_node['viewController'] for vc_node in self.vc_nodes}
        edges = []
        for vc in self.root.iter('viewController'):
            for segue in vc.iter('segue'):
                edge = self.segue_edge(vc_class_name_dict, vc, segue)
                if (edge):
                    edges.append(edge)
        return edges

    def segue_edge(self, vc_class_name_dict, vc, segue):
        if segue.attrib['kind'] == 'presentation':
            dest_vc_id = segue.attrib['destination']
            dest_vc_class_name = vc_class_name_dict[dest_vc_id]
            return { 'id': segue.attrib['id'],
                    'source': vc.attrib['customClass'],
                    'destination': dest_vc_class_name,
                    'identifier': segue.attrib['identifier'],
            }
        return None 

    def collect_relationship_segue_edges(self):
        """
        Return edges representing segues
        """
        # TODO


    def relationship_segue_edge(self, vc_class_name_dict, vc, segue):
        if segue.attrib['kind'] == 'relationship':
            dest_vc_id = segue.attrib['destination']
            dest_vc_class_name = vc_class_name_dict[dest_vc_id]
            return { 'id': segue.attrib['id'],
                    'source': vc.attrib['customClass'],
                    'destination': dest_vc_class_name,
                    'identifier': segue.attrib['identifier'],
            }
        return None 

    def collect_unwind_edges(self):
        """
        Return edges representing unwind segues
        """
        vc_class_names = [vc_node['viewController'] for vc_node in self.vc_nodes]
        edges = []
        for vc in self.root.iter('viewController'):
            for segue in vc.iter('segue'):
                edge = self.unwind_edge(vc_class_names, vc, segue)
                if (edge):
                    edges.append(edge)
        return edges

    def unwind_edge(self, vc_class_names, vc, segue):
        if (segue.attrib['kind'] == 'unwind'):
            identifier = segue.attrib['identifier'] # ends in 'VC'
            identifier_full = identifier.replace('VC', 'ViewController')
            dest_vc_class_name = find_nearest(identifier_full, vc_class_names)
            return { 'id': segue.attrib['id'],
                    'source': vc.attrib['customClass'],
                    'destination': dest_vc_class_name,
                    'identifier': identifier,
            }
        return None 

    ### preliminary investigation

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
            strs.append('')
            #strs.append(self.dump(vc.attrib, ['id']))
            for segue in vc.iter('segue'):
                #     print(segue)
                strs.append('        segue ' + self.dump(segue.attrib, ['id', 'destination', 'kind', 'identifier', 'unwindAction', 'modalPresentationStyle',  'modalTransitionStyle']))
                #{"destination": "aZf-qq-fub", "kind": "presentation", "identifier": "toStickerShopVC", "modalPresentationStyle": "fullScreen", "modalTransitionStyle": "crossDissolve", "id": "Dde-ZG-iRW"}
        return "\n".join(strs)

    def viewControllers_info(self):
        strs = []
        for vc in self.root.iter('viewController'):
            strs.append(json.dumps(vc.attrib))
            strs.append('')
            #strs.append(self.dump(vc.attrib, ['id', 'customClass']))
            for segue in vc.iter('segue'):
                #     print(segue)
                strs.append('        segue ' + self.dump(segue.attrib, ['id', 'destination', 'kind', 'identifier', 'unwindAction', 'modalPresentationStyle',  'modalTransitionStyle']))
                #{"destination": "aZf-qq-fub", "kind": "presentation", "identifier": "toStickerShopVC", "modalPresentationStyle": "fullScreen", "modalTransitionStyle": "crossDissolve", "id": "Dde-ZG-iRW"}
        return "\n".join(strs)

    def segue_info(self):
        strs = ['??']
        for segue in self.root.iter("segue"):
            segueIdentifier = segue.get("identifier")
            #strs.append(segue.tostring())
            strs.append(json.dumps(segue.attrib))
        #return "\n".join(strs)
        return ''

    def nodes_and_edges(self):
        """
        Returns nodes (view controllers) and edges (segues)
        """
        nodes = []
        edges = []
        for vc in self.root.iter('viewController'):
            nodes.append(self.any_vc_node(vc))
            for segue in vc.iter('segue'):
                edges.append(self.any_segue_edge(vc, segue))
        return {'nodes': nodes, 'edges': edges}

    def any_vc_node(self, vc):
        node = { 'id': vc.attrib['id'],
                'viewController': vc.attrib['customClass']
        }
        return node

    def any_segue_edge(self, vc, segue):
        edge = { 'id': segue.attrib['id'],
                'source': vc.attrib['id'],
                'destination': segue.attrib['destination'],
        }
        return edge


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

    print('root_info:', sb.root_info())
    print('navigationControllers_info:', sb.navigationControllers_info())
    print('viewControllers_info:', sb.viewControllers_info())
    print('segue_info:', sb.segue_info())

    ne = sb.nodes_and_edges()

    print_list('nodes', ne['nodes'])
    print_list('edges', ne['edges'])

    print_list('vc_nodes', sb.vc_nodes)
    print_list('segue_edges', sb.segue_edges)
    print_list('unwind_edges', sb.unwind_edges)
if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("filepath", type=str, default=None)
    args = parser.parse_args()
    print("args.filepath=", args.filepath)

    sb = StoryboardParser(args.filepath)
    print_detail_info(sb)
    ds = sb.digraph()
    print(ds)


