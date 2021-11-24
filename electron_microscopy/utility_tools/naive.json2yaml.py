#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 12 10:20:52 2021

@author: kuehbach
"""

import os, sys
import yaml
import json

fnm = '/home/kuehbach/HU_HU_HU/FAIRmatSoftwareDevelopment/Sprint03_EmApplicationDefinition/NXem2d.json'
with open(fnm) as f:
    schema = json.load(f)

with open(fnm + '.yml', 'w') as outfile:
    yaml.dump(schema, outfile, default_flow_style=False)

