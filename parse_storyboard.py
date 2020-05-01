#!/usr/bin/env python

import sys, os
import xml.etree.ElementTree as et
from argparse import ArgumentParser
import json

def dump(dict, key):
    return f'    {key}: {dict[key]}'

class StoryboardParser(object):

    def __init__(self, filepath):
        """Given a filepath to an Xcode .storyboatd file
        initialize the instance parsing the file.
        """
        self.filepath = filepath

        self.tree = et.parse(filepath)
        self.root = self.tree.getroot()

    def root_info(self):
        strs = []
        #strs.append(json.dumps(self.root.tag))
        #strs.append(json.dumps(self.root.attrib))
        strs.append(dump(self.root.attrib, "initialViewController"))
        return "\n".join(strs)
        #return json.dumps(self.root.tag)

PREFIX = ""

segueIdentifiers = {}
controllerIdentifiers = {}
reuseIdentifiers = {}

def addSegueIdentifier(identifier):
    key = identifier[0].upper() + identifier[1:]
    if not key.startswith(PREFIX.upper()):
        key = PREFIX.upper() + key

    segueIdentifiers[key] = identifier

def addControllerIdentifier(identifier):
    key = identifier[0].upper() + identifier[1:]
    if not key.startswith(PREFIX.upper()):
        key = PREFIX.upper() + key

    controllerIdentifiers[key] = identifier

def addReuseIdentifier(identifier):
  key = identifier[0].upper() + identifier[1:]
  if not key.startswith(PREFIX.upper()):
    key = PREFIX.upper() + key

  reuseIdentifiers[key] = identifier

def process_storyboard(file):
    tree = et.parse(file)
    root = tree.getroot()

    for segue in root.iter("segue"):
        segueIdentifier = segue.get("identifier")
        if segueIdentifier == None:
            continue
        addSegueIdentifier(segueIdentifier)

    for controller in root.findall(".//*[@storyboardIdentifier]"):
        controllerIdentifier = controller.get("storyboardIdentifier")
        if controllerIdentifier == None:
            continue
        addControllerIdentifier(controllerIdentifier)

    for cell in root.findall(".//*[@reuseIdentifier]"):
      reuseIdentifier = cell.get("reuseIdentifier")
      if reuseIdentifier == None:
        continue
      addReuseIdentifier(reuseIdentifier)

def writeHeader(file, identifiers):
    constants = sorted(identifiers.keys())

    for constantName in constants:
        file.write("extern NSString * const " + constantName + ";\n")

def writeImplementation(file, identifiers):
    constants = sorted(identifiers.keys())

    for constantName in constants:
        file.write("NSString * const " + constantName + " = @\"" + identifiers[constantName] + "\";\n")


def doit():

    count = os.environ["SCRIPT_INPUT_FILE_COUNT"]
    for n in range(int(count)):
        process_storyboard(os.environ["SCRIPT_INPUT_FILE_" + str(n)])

    with open(sys.argv[1], "w+") as header:
        header.write("/* Generated document. DO NOT CHANGE */\n\n")
        header.write("/* Segue identifier constants */\n")
        header.write("@class NSString;\n\n")
        writeHeader(header, segueIdentifiers)

        header.write("\n")
        header.write("/* Controller identifier constants */\n")

        writeHeader(header, controllerIdentifiers)

        header.write("\n")
        header.write("/* Reuse identifier constants */\n")

        writeHeader(header, reuseIdentifiers)

        header.close()

    with open(sys.argv[2], "w+") as implementation:
        implementation.write("/* Generated document. DO NOT CHANGE */\n\n")
        implementation.write("#import <Foundation/Foundation.h>\n\n")
        writeImplementation(implementation, segueIdentifiers)
        implementation.write("\n")

        writeImplementation(implementation, controllerIdentifiers)
        implementation.write("\n")

        writeImplementation(implementation, reuseIdentifiers)
        implementation.write("\n")

        implementation.close()

def print_dict(name, dict):
    print(name, ":")
    for key, value in dict.items():
        print("    ", key, value)

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("filepath", type=str, default=None)
    # parser.add_argument("-d", default=',')
    # parser.add_argument("-w", default=150, type=int)
    args = parser.parse_args()

    print("args.filepath=", args.filepath)
    # print("args.d=", args.d)
    # print("args.w=", args.w)

    process_storyboard(args.filepath)

    # print("controllerIdentifiers=", controllerIdentifiers)
    # print("segueIdentifiers=", segueIdentifiers)
    # print("reuseIdentifiers=", reuseIdentifiers)

    # print_dict("controllerIdentifiers", controllerIdentifiers)
    # print_dict("segueIdentifiers", segueIdentifiers)
    # print_dict("reuseIdentifiers", reuseIdentifiers)

    sb = StoryboardParser(args.filepath)

    print(sb.root_info())
