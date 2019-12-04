# coding: utf-8

# Import necesary modules
import sys
import os
import gzip
import re
import emoji
import glob
import subprocess
import vcfpy
import time
import os.path

import pandas as pd
import numpy as np

from halo import Halo
from timeit import default_timer as timer
from subprocess import call

# import functions from scripts
from .parse_argv import parse_commandline
from .split import split
from .decorator import tags


def main():
    # aesthetics
    description = '''

    ----------------------------------------- Welcome to ----------------------------------------------

    $$$$$$$\  $$$$$$$\  $$$$$$$\   
    $$  __$$\ $$  __$$\ $$  __$$\     
    $$ |  $$ |$$ |  $$ |$$ |  $$ |$$$$$$\$$$$\   $$$$$$\   $$$$$$\   $$$$$$\   $$$$$$\   $$$$$$\ 
    $$$$$$$  |$$ |  $$ |$$$$$$$\ |$$  _$$  _$$\  \____$$\ $$  __$$\ $$  __$$\ $$  __$$\ $$  __$$\ 
    $$  ____/ $$ |  $$ |$$  __$$\ $$ / $$ / $$ | $$$$$$$ |$$ /  $$ |$$ /  $$ |$$$$$$$$ |$$ |  \__|
    $$ |      $$ |  $$ |$$ |  $$ |$$ | $$ | $$ |$$  __$$ |$$ |  $$ |$$ |  $$ |$$   ____|$$ |
    $$ |      $$$$$$$  |$$$$$$$  |$$ | $$ | $$ |\$$$$$$$ |$$$$$$$  |$$$$$$$  |\$$$$$$$\ $$ |
    \__|      \_______/ \_______/ \__| \__| \__| \_______|$$  ____/ $$  ____/  \_______|\__|
                                                            $$ |      $$ |
                                                            $$ |      $$ |
                                                            \__|      \__|

    ---------------  Map annotated genomic variants to protein interfaces data in 3D. -----------------

    '''
    # print ascii art
    print(description)
    # initialize spinner decorator
    spinner = Halo(text='Loading', spinner='dots12', color="red")
    # parse command line options
    args = parse_commandline()

    # set out dir and out file names
    # created by default
    out_dir = os.path.join(args.out, 'DBs')
    # out_file = os.path.join(
    #    out_dir, 'variants.vep')  # created by default
    # set output dir to split vep
    intdb_outdir = os.path.join(out_dir, 'intDB')  # created by default
    # create output dir if it doesn't exist
    os.makedirs(intdb_outdir, exist_ok=True)

    # split interface db
    split('ENSP', args.intdb, intdb_outdir, 'txt', args.force)
    # set origin of input interface
    #    input_intdb = 'external'
    # else:
    #    spinner.info(text='Default interfaces DB is used.')
    #    # set default interfaces database
    #    int_db_dir = "/home/vruizser/PhD/2018-2019/git/PDBmapper/default_input_data/splitted_interfaces_db"
    # set origin of input interface
    #    input_intdb = 'default'
