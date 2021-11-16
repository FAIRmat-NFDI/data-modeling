#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 12 10:20:52 2021
@author: kuehbach
"""

import os, sys
import yaml
#import punx
#import json
from lxml import etree

def nx_base_clss_string_mangling(tmp):
    if tmp[0:3] == 'nx_':
        return 'NX_'+tmp[3::]
    else:
        return tmp
        #raise ValueError(tmp+' is not a properly formatted nexus keyword which this parser knows!')

fnm = '/home/kuehbach/HU_HU_HU/FAIRmatSoftwareDevelopment/Sprint03_EmApplicationDefinition/issue_xx_yaml2nxdl/NXmx.yml'
with open(fnm) as stream:
    try:
        yml = yaml.safe_load(stream)
        #print(yml)
        #rt = etree.Element('description')
    except yaml.YAMLError as exc:
        print(exc)

nx_base_clss = ['nx_aperture', 'nx_attenuator', 'nx_beam', 'nx_beam_stop', 'nx_bending_magnet', 'nx_capillary', 'nx_cite', 
    'nx_collection', 'nx_collimator', 'nx_crystal', 'nx_cylindrical_geometry', 'nx_data', 'nx_detector', 
    'nx_detector_group', 'nx_detector_module', 'nx_disk_chopper', 'nx_entry', 'nx_environment', 'nx_event_data', 
    'nx_fermi_chopper', 'nx_filter', 'nx_flipper', 'nx_fresnel_zone_plate, ''nx_geometry', 'nx_grating', 'nx_guide', 
    'nx_insertion_device', 'nx_instrument', 'nx_log', 'nx_mirror', 'nx_moderator', 'nx_monitor', 'nx_monochromator', 
    'nx_note', 'nx_object', 'nx_off_geometry', 'nx_orientation', 'nx_parameters', 'nx_pdb', 'nx_pinhole', 'nx_polarizer', 
    'nx_positioner', 'nx_process', 'nx_reflections', 'nx_root', 'nx_sample', 'nx_sample_component', 'nx_sensor', 'nx_shape', 
    'nx_slit', 'nx_source', 'nx_subentry', 'nx_transformations', 'nx_translation', 'nx_user', 'nx_velocity_selector',
    'nx_xraylens']
nx_type_keys = ['nx_date_time', 'nx_char', 'nx_number', 'nx_float', 'nx_uint', 'nx_int', 'nx_boolean']
nx_attr_idnt = '\@'
nx_unit_idnt = 'units'


def recursive_build(obj, dict_value):
    """
    obj is the current node where we want to append to
    dctv is value for a key in a (nested) dictionary
    """
    for k, v in iter(dict_value.items()):
        print('Processing '+k)
        if not isinstance(v, dict): #if value v is not a dictionary, we should be in the definitions part of the NXDL schema
            if k[0:2] == nx_attr_idnt: #if we have an attribute
                attr = etree.SubElement(obj, 'attribute')
                attr.set('name', k[1:])
                ###MK::start a new recursion ??
            else: #is not an attribute
                if k == 'name': #is key a name?
                    obj.set('name', v)
                elif k == 'type': #is key a type?
                    if v in nx_type_keys:
                        obj.set(k, v.upper())
                    elif v in nx_base_clss:
                        obj.set(k, nx_base_clss_string_mangling(v))
                    else:
                        print('WARNING: key: '+k+' value: '+str(v)+' is not one of predefined type keys')
                elif k == 'doc': #key is a documentation string specifier
                    #child = obj.SubElement('doc', v)
                    #child.set('doc', v)
                    obj.set('doc', v)
                elif k in nx_base_clss: #is key an instance of an nx_base_clss?
                    print('WARNING: '+k+' is a base class but value v is not a dictionary !')
                elif k == nx_unit_idnt:
                    obj.set('units', v.upper())
                elif k == 'exists':
                    if v == 'optional':
                        obj.set('optional', 'true')
                    elif v == 'recommended':
                        obj.set('recommended', 'true')
                    elif v == 'required':
                        obj.set('required', 'true')
                    else:
                        obj.set('minOccurs', '0')
                elif k == 'enumeration': #if we face an enumeration
                    enum = etree.SubElement(obj, 'enumeration')
                    print('Processing enumeration')
                    #assume we get a list as the value argument
                    if isinstance(v, list):
                        for m in v:
                            itm = etree.SubElement(enum, 'item')
                            itm.set('value', str(m))
                    else:
                        raise ValueError('ERROR: '+k+' we found an enumeration key-value pair but the value is not an ordinary Python list !')
                #
                elif k == 'rank':
                    obj.set('rank', str(v))
                elif k == 'dim':
                    if isinstance(v,list):
                        for m in v:
                            if isinstance(m, list):
                                if len(m) >= 2:
                                    dim = etree.SubElement(obj, 'dim')
                                    dim.set('index', str(m[0]))
                                    dim.set('value', str(m[1]))
                                    if len(m) == 3:
                                        if m[2] == 'optional':
                                            dim.set('required', 'false')
                                        else:
                                            print('WARNING: '+k+' dimensions with len(3) list with non-optional argument, unexpected case !')
                                else:
                                    raise ValueError('WARNING: '+k+' dimensions list item needs to have at least two members !' )
                    else:
                        raise ValueError('ERROR: '+k+' we found an dimensions key-value pair but the value is not an ordinary Python list of list !')
                #
                elif v == None:
                    obj.set('name', k)
                else:
                    print('WARNING: '+k+' we found an unexpected case !')
        else: #dictionary value is again a dictionary, we can face am attribute, symbols, a base class or a field
            if k[0:2] == nx_attr_idnt: #if we have an attribute
                attr = etree.SubElement(obj, 'attribute')
                attr.set('name', k[1:])
                recursive_build(attr, v)
            elif k == 'symbols': #if we face symbols
                syms = etree.SubElement(obj, 'symbols')
                print('Processing symbols')
                for kk, vv in iter(v.items()):
                    if kk == 'doc':
                        syms.set('doc', vv)
                    else:
                        sym = etree.SubElement(syms, 'sym')
                        sym.set('name', kk)
                        sym.set('doc', vv)
            elif k == 'dimensions': #if we face a dimensions
                dims = etree.SubElement(obj, 'dimensions')
                recursive_build(dims, v)
            elif k in nx_base_clss: ##if we have a base class ##MK::suggestion for the future, invert logic list of type keys check if k in nx_type_key (type keys only attribute or fields)
                grp = etree.SubElement(obj, 'group')
                grp.set('type', nx_base_clss_string_mangling(k))
                recursive_build(grp, v)
            else: #if we have a field
                if k[0:2] == nx_attr_idnt: #if we have an attribute of a field)
                    attr = etree.SubElement(obj, 'attribute')
                    attr.set('name', k[1:])
                    recursive_build(attr, v)
                else: #not an attribute, so an ordinary field
                    fld = etree.SubElement(obj, 'field')
                    fld.set('name', k)
                    if 'exists' in v:
                        if v['exists'] == 'optional':
                            fld.set('optional', 'true')
                        elif v['exists'] == 'recommended':
                            fld.set('recommended', 'true')
                        elif v['exists'] == 'required':
                            fld.set('required', 'true')
                        else:
                            fld.set('minOccurs', '0') #print('Unknown exists case !')
                    ###MK::set minOccurs = 0 by default
                    #else:
                    #    addition.set('minOccurs', '0') #print('Unknown exists case !')
                    recursive_build(fld, v)
            #recursive_build(obj, v)


rt = etree.Element('definition')
recursive_build(rt, yml)

nxdl = etree.ElementTree(rt)
nxdl.write( fnm + '.nxdl', pretty_print=True, xml_declaration=True, encoding="utf-8" )
print('Parsed YAML to NXDL')



##recursive_build(rt, yml['magic'])
##entry = etree.SubElement(rt, 'nx_entry') #'group'
##recursive_build(entry, yml['nx_entry'])















# =============================================================================
# def is_leaf(pth, dct):
#     """
#     checks if path pth in a dictionary dct is a leaf, i.e. a value which is no longer a dictionary
#     """
#     pth = 'entry1/mygroup'
#     #tmpdct = dct
#     nodes = pth.split('/') #nodes along the path to resolve nested dictionaries
#     currpath = ''
#     #is_leaf = True #argue by falsification
#     for i in nodes:
#         currpath += '/' + i
#         #currpath = '/entry1'
#         print(currpath[1::])
#         if currpath[1::] in tmpdct:
#             tmpdct = tmpdct[i]
#             if currpath[1::] != pth:
#                 continue #traverse down
#             else:
#                 #arrived at the target path
#                 for k, v in tmpdct[i].items():
#                     if type(v) == dict:
#                         is_leaf = False
#                         print('False')
#                 print('True')
#         else:
#             raise ValueError('Path ' + currpath[1::] +' is not resolvable for dictionary !')
#             
# a = is_leaf('entry1/my_group', yml)
#         
# 
# class yml2nxdl():
#     def __init__(self, fnm, *args, **kwargs):
#         self.yml = {}
#         self.rt = None
#         self.fnm = fnm
#         with open(self.fnm) as stream:
#             try:
#                 self.yml = yaml.safe_load(stream)
#                 print(self.yml)
#                 rt = etree.Element('description')
#             except yaml.YAMLError as exc:
#                 print(exc)
#     
#     def set_root(self):
#         if 'magic' in yml:
#             if 'name' in yml['magic']:
#                 rt.set("name", yml['magic']['name'])
#             if 'doc' in yml['magic']:
#                 rt.set("doc", yml['magic']['doc'])
#             else:
#                 #MK::accept default for NXobject
#                 pass
#             
#     def set_entry(self):
#         if len(yml) == 2:
#             
#             pass
#         else:
#             raise ValueError('Current implementation supports that there is only one NXentry group')
#                 
#     def write_nxdl(self):
#         nxdl = etree.ElementTree(rt)
#         nxdl.write( fnm + '.nxdl', pretty_print=True, xml_declaration=True, encoding="utf-8" )
# 
#                 
# for k in yml[entry].keys():
#     if not isinstance(yml[k],dict):
#         
#             
# rt = etree.Element('description')
# #tmp = etree.Element('doc')
# nxdl = etree.ElementTree(rt)
# nxdl.write( fnm + '.nxdl', pretty_print=True, xml_declaration=True, encoding="utf-8" )
# 
# 
# rt = etree.Element('description')
# if 'magic' in yml:
#     if 'name' in yml['magic']:
#         rt.set("name", yml['magic']['name'])
#     if 'doc' in yml['magic']:
#         rt.set("doc", yml['magic']['doc'])
#     else:
#         #MK::accept default for NXobject
#         pass
#     
# if 'entry' in yml:
#     if isinstance(yml['entry'], dict):
# =============================================================================

#TO DO:
#stylesheet information missing
#<?xml-stylesheet type="text/xsl" href="nxdlformat.xsl" ?>
