#!/usr/bin/env python3
# coding: utf-8
import subprocess
import sys
from scripts.decorator import tags
 
 # ./vep -i input.vcf -o out.txt -offline
 
def run_vep():
    cmd = "./vep -i input.vcf -o out.txt -offline"
    p = subprocess.Popen(cmd,  stdout=subprocess.PIPE, stderr=log, shell=True)
    