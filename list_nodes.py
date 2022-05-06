#!/usr/bin/python
# Script that prints nodes in specific state to terminal
# uses SLURM sinfo command
# 2018 Colleen Rooney
from sinfo_parsing import *
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--partition", help="get nodes from specified partition")
parser.add_argument("-s", "--state", help="list nodes in a state other than \
idle")
parser.add_argument("-v", "--verbose", action="store_true", help="prints the name of the \
partition the node is in to stdout after the name of the node")
args = parser.parse_args()

partition = args.partition if args.partition else ''
state = args.state if args.state else 'idle'


nodes = get_nodes(partition=partition, state=state)

for node in nodes:
    part = node['partition'] if args.verbose else ''
    print("%s %s" % (node['node'], part))