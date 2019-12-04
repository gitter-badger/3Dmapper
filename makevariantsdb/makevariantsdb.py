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
from .run_vep import run_vep
from .split import split
from .detect_vcf_format import detect_format
from .vcf2vep import vcf2vep
from .maf2vep import maf2vep
from .add_header import add_header
from .decorator import tags


class generateVarDB:

    def vcf(self, var_path, out_dir, out_file, vcf_db_dir, overwrite):
        # from vcf to vep
        vcf2vep(var_path, out_dir,
                out_file, overwrite)
        # add header to resulting vep file
        add_header(out_file)
        # split vep file by protein id to speed up the
        # mapping process
        split('ENSG', out_file, vcf_db_dir,
              'vep', overwrite)

    def vep(self, var_path, vcf_db_dir, overwrite):
        # split vep file by protein id to speed up the
        # mapping process
        split('ENSG', var_path, vcf_db_dir,
              'vep', overwrite)

    def maf(self, var_path, out_dir, out_file, vcf_db_dir, overwrite):
        # from vcf to vep
        maf2vep(var_path, out_dir,
                out_file, overwrite)
        # split vep file by protein id to speed up the
        # mapping process
        split('ENSG', out_file, vcf_db_dir,
              'vep', overwrite)


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
    out_file = os.path.join(
        out_dir, 'variants.vep')  # created by default
    # set output dir to split vep
    vcf_db_dir = os.path.join(out_dir, 'varDB')  # created by default
    # create output dir if it doesn't exist
    os.makedirs(vcf_db_dir, exist_ok=True)
    # initialize class
    varfile = generateVarDB()

    # change input format if file doesn't exists or overwrite is True
    if not os.listdir(vcf_db_dir) or args.force.lower() == 'y':

        if args.vcf is not None:
            # for loop in case we have multiple inputs to read from a list of files
            for f in args.vcf:
                # check if input is a file
                try:
                    with open(f) as list_var_files:
                        var_f = list_var_files.read().splitlines()
                        # for every prot id
                        for var_path in var_f:
                            # detect the format of the vcf file(s), either .vcf or .vep
                            input_format = detect_format(var_path)
                            # If vcf transform into vep format and split
                            if input_format == "vcf":
                                # change input format if file doesn't exists or overwrite is True
                                if os.path.isfile(out_file) is False or args.force.lower() == 'y':
                                    # split vcf file
                                    varfile.vcf(var_path, out_dir,
                                                out_file, vcf_db_dir, args.force)

                            # If vep, only split
                            elif input_format == "vep":
                                # split if empty dir or overwrite is True
                                if not os.listdir(vcf_db_dir) or args.force.lower() == 'y':
                                    # split vep file by protein id to speed up the
                                    # mapping process
                                    varfile.vep(
                                        var_path, vcf_db_dir, args.force)
                            else:
                                print('Warning: input file ' + var_path +
                                      ' is not in vep nor vcf format.')
                                continue

                except:
                    # change input format if file doesn't exists or overwrite is True
                    if not os.listdir(vcf_db_dir) or args.force.lower() == 'y':
                        # detect the format of the vcf file(s), either .vcf or .vep
                        input_format = detect_format(f)
                        # If vcf transform into vep format and split
                        if input_format == "vcf":
                            # change input format if file doesn't exists or overwrite is True
                            if os.path.isfile(out_file) is False or args.force.lower() == 'y':
                                # split vcf file
                                varfile.vcf(f, out_dir,
                                            out_file, vcf_db_dir, args.force)

                        # If vep, only split
                        elif input_format == "vep":
                            # split if empty dir or overwrite is True
                            if not os.listdir(vcf_db_dir) or args.force.lower() == 'y':
                                # split vep file by protein id to speed up the
                                # mapping process
                                varfile.vep(f, vcf_db_dir, args.force)

                        else:
                            print('Warning: input file ' + var_path +
                                  ' is not in vep nor vcf format.')
                            continue

        # If MAF transform into VEP format and split
        elif args.maf is not None:
            # for loop in case we have multiple inputs to read from a list of files
            for f in args.maf:
             # check if input is a file
                try:
                    with open(f) as list_var_files:
                        var_f = list_var_files.read().splitlines()
                        # for every prot id
                        for var_path in var_f:
                            # change input format if file doesn't exists or overwrite is True
                            if os.path.isfile(out_file) is False or args.force.lower() == 'y':
                                # split MAF file
                                varfile.maf(var_path, out_dir,
                                            out_file, vcf_db_dir, args.force)
                except:
                    # change input format if file doesn't exists or overwrite is True
                    if not os.listdir(vcf_db_dir) or args.force.lower() == 'y':
                        # split MAF file
                        varfile.maf(f, out_dir,
                                    out_file, vcf_db_dir, args.force)
        elif args.vep is not None:
            spinner.warn(text='VEP option will be available soon. Using VarMap db instead. \
    Otherwise, please provide your own vcf file with the -vcf option.\n')
            try:
                run_vep()
            except IOError:
                vcf_db_dir = '/home/vruizser/PhD/2018-2019/git/PDBmapper/default_input_data/splitted_ClinVar'
                spinner.info('Using VarMap db\n')
                exit(-1)
        elif args.varmap is not None:
            spinner.info('Using VarMap db')
            vcf_db_dir = '/home/vruizser/PhD/2018-2019/git/PDBmapper/default_input_data/splitted_ClinVar'
    else:
        print('A variants database already exists.')