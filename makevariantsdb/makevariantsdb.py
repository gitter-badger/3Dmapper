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
import os.path as path

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


# class logfile(object):
#     # Current Day
#     Day = time.strftime("%d-%m-%Y", time.localtime())
#     # Current Time
#     Time = time.strftime("%I:%M:%S %p", time.localtime())
#     # Date and Time to display next to the message
#     dt = '[' + Day + ']' + Time + ' '

#     def __enter__(self, file_location):
#         self.log_file = open(file_location, 'a+')
#         return self

#     def write(self, message):
#         self.log_file.write(dt + message)

#     def __exit__(self):
#         self.log_file.close()


class generateVarDB:
    # Current Day
    Day = time.strftime("%d-%m-%Y", time.localtime())
    # Current Time
    Time = time.strftime('%H:%M:%S', time.localtime())
    # Date and Time to display next to the message
    dt = '[' + Day + '] ' + Time + ' '

    def vcf(self, var_infile, out_dir, out_file, vardb_outdir, overwrite):

        # initialize log file
        #log = open(os.path.join(out_dir, 'makevariants.log'), 'a')
        log.write('Transforming vcf to vep...\n')

        # from vcf to vep
        vcf2vep(var_infile, out_dir,
                out_file, overwrite)
        # add header to resulting vep file
        add_header(out_file)

        log.write(self.dt + ' Splitting vep file...\n')
        # split vep file by protein id to speed up the
        # mapping process
        split('ENSG', out_file, vardb_outdir,
              'vep', overwrite)

        log.write(self.dt + ' Splitting vep file...done.\n')

    def vep(self, var_infile, vardb_outdir, overwrite):

        # initialize log file
        #log = open(os.path.join(vardb_outdir, 'makevariants.log'), 'a')
        log.write(self.dt + ' Splitting vep file...\n')
        # split vep file by protein id to speed up the
        # mapping process
        split('ENSG', var_infile, vardb_outdir,
              'vep', overwrite)
        log.write(self.dt + ' Splitting vep file...done.\n')

    def maf(self, var_infile, out_dir, out_file, vardb_outdir, overwrite):
        # from vcf to vep
        maf2vep(var_infile, out_dir,
                out_file, overwrite)
        # split vep file by protein id to speed up the
        # mapping process
        split('ENSG', out_file, vardb_outdir,
              'vep', overwrite)


def main():
    # parse command line options
    args = parse_commandline()
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
    # Log file
    log = open(os.path.join(args.out, 'makevariants.log'), 'a')
    log.write(description)
    # print ascii art
    print(description)
    # initialize spinner decorator
    spinner = Halo(text='Loading', spinner='dots12', color="red")
    # set out dir and out file names
    # created by default
    out_dir = os.path.join(args.out, 'DBs')
    out_file = os.path.join(
        out_dir, 'variants.vep')  # created by default
    # set output dir to split vep
    vardb_outdir = os.path.join(out_dir, 'varDB')  # created by default
    # create output dir if it doesn't exist
    os.makedirs(vardb_outdir, exist_ok=True)
    # initialize class
    varfile = generateVarDB()

    # change input format if file doesn't exists or overwrite is True
    if not os.listdir(vardb_outdir) or args.force.lower() == 'y':
        # Manage all possible genomic variant input files
        if args.vcf is not None:
            # for loop in case we have multiple inputs to read from a list of files
            for f in args.vcf:
                # check if input is a file
                try:
                    with open(f) as list_var_files:
                        var_f = list_var_files.read().splitlines()
                        # for every prot id
                        for var_infile in var_f:
                            # detect the format of the vcf file(s), either .vcf or .vep
                            input_format = detect_format(var_infile)
                            # If vcf transform into vep format and split
                            if input_format == "vcf":
                                # change input format if file doesn't exists or overwrite is True
                                if os.path.isfile(out_file) is False or args.force.lower() == 'y':
                                    # split vcf file
                                    varfile.vcf(var_infile, out_dir,
                                                out_file, vardb_outdir, args.force)

                            # If vep, only split
                            elif input_format == "vep":
                                # split if empty dir or overwrite is True
                                if not os.listdir(vardb_outdir) or args.force.lower() == 'y':
                                    # split vep file by protein id to speed up the
                                    # mapping process
                                    varfile.vep(
                                        var_infile, vardb_outdir, args.force)
                            else:
                                print('Warning: input file', var_infile,
                                      'is not in vep nor vcf format.')
                                continue

                except:
                    # change input format if file doesn't exists or overwrite is True
                    if not os.listdir(vardb_outdir) or args.force.lower() == 'y':
                        # detect the format of the vcf file(s), either .vcf or .vep
                        input_format = detect_format(f)
                        # If vcf transform into vep format and split
                        if input_format == "vcf":
                            # change input format if file doesn't exists or overwrite is True
                            if os.path.isfile(out_file) is False or args.force.lower() == 'y':
                                # split vcf file
                                varfile.vcf(f, out_dir,
                                            out_file, vardb_outdir, args.force)

                        # If vep, only split
                        elif input_format == "vep":
                            # split if empty dir or overwrite is True
                            if not os.listdir(vardb_outdir) or args.force.lower() == 'y':
                                # split vep file by protein id to speed up the
                                # mapping process
                                varfile.vep(f, vardb_outdir, args.force)

                        else:
                            print('Warning: input file', var_infile,
                                  'is not in vep nor vcf format.')
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
                        for var_infile in var_f:
                            # change input format if file doesn't exists or overwrite is True
                            if os.path.isfile(out_file) is False or args.force.lower() == 'y':
                                # split MAF file
                                varfile.maf(var_infile, out_dir,
                                            out_file, vardb_outdir, args.force)
                except:
                    # change input format if file doesn't exists or overwrite is True
                    if not os.listdir(vardb_outdir) or args.force.lower() == 'y':
                        # split MAF file
                        varfile.maf(f, out_dir,
                                    out_file, vardb_outdir, args.force)
        elif args.vep is not None:
            spinner.warn(text='VEP option will be available soon. Using VarMap db instead. \
    Otherwise, please provide your own vcf file with the -vcf option.\n')
            try:
                run_vep()
            except IOError:
                vardb_outdir = '/home/vruizser/PhD/2018-2019/git/PDBmapper/default_input_data/splitted_ClinVar'
                spinner.info('Using VarMap db\n')
                exit(-1)
        elif args.varmap is not None:
            spinner.info('Using VarMap db')
            vardb_outdir = '/home/vruizser/PhD/2018-2019/git/PDBmapper/default_input_data/splitted_ClinVar'
    else:
        print('A variants database already exists.')
