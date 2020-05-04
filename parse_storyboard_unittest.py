#!/usr/local/bin/python
#
#  parse_storyboard_unittest.py v.0.1.0
#  Tests for parse_storyboard.py
#
#  Created by Rudolf Farkas on 04.05.2020
#  Copyright © 2020 Rudolf Farkas. All rights reserved.
#

import unittest
import json
from parse_storyboard import StoryboardParser

class StoryboardParser_unittest(unittest.TestCase):

    def setUp(self):
        self.filepath = 'sample.storyboard'

    def test_parser(self):
        sb = StoryboardParser(self.filepath, plot=False)

        self.assertEqual(sb.root_info(), '    initialViewController: rS3-R9-Ivy')

        dict_string = str(sb.controller_name_dict)
        expected = "{'Ah7-4n-0Wa': 'JBWDetailViewController', 'rS3-R9-Ivy': 'navigationController-rS3-R9-Ivy', 'pGg-6v-bdr': 'JBWMasterViewController'}"
        self.assertEqual(dict_string, expected)

        segue_edges_string = sb.segue_edges
        self.assertEqual(str(segue_edges_string[0]), "{'id': 'RxB-wf-QIq', 'source': 'navigationController-rS3-R9-Ivy', 'destination': 'JBWMasterViewController', 'identifier': 'navigation', 'kind': 'relationship'}")
        self.assertEqual(str(segue_edges_string[1]), "{'id': 'jUr-3t-vfg', 'source': 'JBWMasterViewController', 'destination': 'JBWDetailViewController', 'identifier': 'showDetailIdentifier', 'kind': 'push'}")              
   
        expected = """\
digraph storyboard {
\tnode [fontname=courier fontsize=12 shape=rect]
\tedge [fontname=courier fontsize=10]
\t"" [label="sample.storyboard" shape=none]
\t"" -> "navigationController-rS3-R9-Ivy"
\tJBWDetailViewController
\t"navigationController-rS3-R9-Ivy"
\tJBWMasterViewController
\t"navigationController-rS3-R9-Ivy" -> JBWMasterViewController [label=navigation color=black]
\tJBWMasterViewController -> JBWDetailViewController [label=showDetailIdentifier color=black]
}"""
        self.maxDiff = None
        self.assertEqual(sb.digraph(), expected)



if __name__ == "__main__":
    unittest.main()
