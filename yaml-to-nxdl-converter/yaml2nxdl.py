#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 12 10:20:52 2021
@author: kuehbach
"""

import os, sys
import yaml
from lxml import etree
from yaml2nxdl_utils import nx_base_clss_string_mangling
from yaml2nxdl_utils import nx_base_clss, nx_cand_clss, nx_unit_idnt, nx_unit_typs
from yaml2nxdl_utils import nx_type_keys, nx_attr_idnt
from yaml2nxdl_read_user_yml_appdef import read_user_appdef
from yaml2nxdl_recursive_build import recursive_build


#fnm = 'NXarpes.yml'
#fnm = 'NXmx.yml'
#fnm = 'NXem_base_draft.yml'
#fnm = 'NXellipsometry_base_draft.yml'
fnm = './ARPES/Application_Definitions/NXmpes_core_draft.yml'

#step1: read the user-specific application definition which was written as a yml file
yml = read_user_appdef(fnm)

#step2a: create an instantiated NXDL schema XML tree, begin with the header, XML schema and namespaces
attr_qname = etree.QName("http://www.w3.org/2001/XMLSchema-instance", "schemaLocation")
rt = etree.Element('definition',
                   {attr_qname: 'http://definition.nexusformat.org/nxdl/nxdl.xsd' },
                   nsmap = {None: 'http://definition.nexusformat.org/nxdl/3.1',
                            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'})


#step2b: user-defined attributes for the root group
rt.set('category', 'application')
pi = etree.ProcessingInstruction("xml-stylesheet", text='type="text/xsl" href="nxdlformat.xsl"')
rt.addprevious(pi)
if 'name' in yml.keys():
    rt.set('name', yml['name'])
    del yml['name']
else:
    raise ValueError('ERROR: name: keyword not specified !')
rt.set('extends', nx_base_clss_string_mangling('nx_object'))
rt.set('type', 'group')
if 'doc' in yml.keys():
    rt.set('doc', yml['doc'])
    del yml['doc']
else:
    raise ValueError('ERROR: doc: keyword not specified !')
if 'symbols' in yml.keys():
    syms = etree.SubElement(rt, 'symbols')
    if 'doc' in yml['symbols'].keys():
        syms.set('doc', yml['symbols']['doc'])
        del yml['symbols']['doc']
    for kk, vv in iter(yml['symbols'].items()):
        sym = etree.SubElement(syms, 'sym')
        sym.set('name', kk)
        sym.set('doc', vv)
    del yml['symbols']
#do not throw in the case of else then we have no symbols

#step3: create an instantiated NXDL schema XML tree, continue with the body of the application definition

recursive_build(rt, yml)

#step4: write the NXDL XML file to file
nxdl = etree.ElementTree(rt)
nxdl.write( fnm + '.nxdl.xml', pretty_print=True, xml_declaration=True, encoding="utf-8" )
print('Parsed YAML to NXDL')
