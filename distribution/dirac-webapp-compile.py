#!/usr/bin/env python3
"""
This is used to compile WebAppDIRAC and its extension, if exists
"""
import os
import argparse

from WebAppCompiler import WebAppCompiler

parser = argparse.ArgumentParser()

parser.add_argument("-n", "--name", help="tarball name")
parser.add_argument("-D", "--destination", help="Destination where to build the tar files")
parser.add_argument("-P", "--extjspath", help="directory of the extjs library")

args = parser.parse_args()
args.destination == os.path.realpath(args.destination)

WebAppCompiler(args.name, args.destination, args.extjspath).run()
