#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 22 17:48:21 2021

@author: kuehbach
"""
import os, sys
import yaml
from lxml import etree
from yaml2nxdl_utils import nx_base_clss_string_mangling
from yaml2nxdl_utils import nx_base_clss, nx_cand_clss, nx_unit_idnt, nx_unit_catg
from yaml2nxdl_utils import nx_type_keys, nx_grpnm_tag, nx_attr_idnt

def xml_handle_exists(obj, k, v):
    if v != None:
        if isinstance(v,list):
            if len(v) == 2:
                if v[0] == 'min':
                    obj.set('minOccurs', str(v[1]))
                if v[0] == 'max':
                    obj.set('maxOccurs', str(v[1]))
            elif len(v) == 4:
                if v[0] == 'min' and v[2] == 'max':
                    obj.set('minOccurs', str(v[1]))
                    if str(v[3]) != 'infty':
                        obj.set('maxOccurs', str(v[3]))
                    else:
                        obj.set('maxOccurs', 'unbounded')
                else:
                    raise ValueError('exists keyword needs to go either with optional, recommended, a list with two entries either [min, <uint>] or [max, <uint>], or a list of four entries [min, <uint>, max, <uint>] !')
            else:
                raise ValueError('exists keyword needs to go either with optional, recommended, a list with two entries either [min, <uint>] or [max, <uint>], or a list of four entries [min, <uint>, max, <uint>] !')
        else:
            if v == 'optional':
                obj.set('optional', 'true')
            elif v == 'recommended':
                obj.set('recommended', 'true')
            #elif v == 'required':
            #    obj.set('required', 'true')
            else:
                obj.set('minOccurs', '0')
    else:
        raise ValueError('exists keyword found but value is None !')

def xml_handle_dimensions(obj, k, v):
    if v != None:
        if isinstance(v,dict):
            if 'rank' in v and 'dim' in v:
                dims = etree.SubElement(obj, 'dimensions')
                dims.set('rank', str(v['rank']))
                for m in v['dim']:
                    if isinstance(m, list):
                        if len(m) >= 2:
                            dim = etree.SubElement(dims, 'dim')
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
                raise ValueError('exists keyword found, value is dict but has no keys rank and dim !')
        else:
            raise ValueError('exists keyword found but value is not a dictionary !')
    else:
        raise ValueError('exists keyword found but value is None !')

def xml_handle_enumeration(obj, k, v):
    enum = etree.SubElement(obj, 'enumeration')
    #assume we get a list as the value argument
    if v != None:
        if isinstance(v, list):
            for m in v:
                itm = etree.SubElement(enum, 'item')
                itm.set('value', str(m))
        else:
            raise ValueError('ERROR: '+k+' we found an enumeration key-value pair but the value is not an ordinary Python list !')
    else:
        raise ValueError('ERROR: '+k+' we found an enumeration key-value pair but the value is None !')


def recursive_build(obj, dct):
    """
    obj is the current node where we want to append to, dct is a dictionary object which represents the content of the child in the nested set of dictionaries
    """
    for k, v in iter(dct.items()):
        print('Processing key '+k+' value v is a dictionary '+str(isinstance(v,dict)))
        #base class prefix tag removal
        if nx_grpnm_tag in k: #k is a group for sure because only groups may get tagged !
            grpnm, grptyp = k.split(nx_grpnm_tag)
            #create a group, set its type and name, and recurse
            grp = etree.SubElement(obj, 'group')
            grp.set('name', grpnm)
            grp.set('type', nx_base_clss_string_mangling(grptyp))
            if v != None:
                if isinstance(v,dict):
                    if v != {}:
                        recursive_build(grp, v)
        elif k in nx_base_clss or k in nx_cand_clss: #k is also a group for sure
            grp = etree.SubElement(obj, 'group')
            #grp.set('name', '') ###MK::??
            grp.set('type', nx_base_clss_string_mangling(k))
            if v != None:
                if isinstance(v,dict):
                    if v != {}:
                        recursive_build(grp, v)
        elif k[0:2] == nx_attr_idnt: #k tells us we have an attribute
            attr = etree.SubElement(obj, 'attribute')
            attr.set('name', k[2:])
            if v != None:
                if isinstance(v,dict):
                    for kk, vv in iter(v.items()):
                        if kk == 'name':
                            attr.set('name', vv)
                        elif kk == 'doc':
                            attr.set('doc', vv)
                        elif kk == 'type':
                            attr.set('type', vv.upper())
                        elif kk == 'enumeration':
                            xml_handle_enumeration(attr,kk, vv)
                        else:
                            raise ValueError('ERROR: '+kk+' faced unknown situation when processing attributes of an attribute !')
            #else: #e.g. for case like \@depends_on:
            #    attr.set('name', k[2:])
        elif k == 'doc':
            obj.set('doc', v)
        elif k == 'enumeration': #if we face an enumeration
            xml_handle_enumeration(obj, k, v)
        elif k == 'dimensions':
            xml_handle_dimensions(obj, k, v)
        elif k == 'exists':
            xml_handle_exists(obj, k, v)
        else: #k is for a field
            fld = etree.SubElement(obj, 'field')
            fld.set('name', k)
            if v != None:
                #the field may have subordinated field XML attributes
                if isinstance(v,dict):
                    for kk, vv in iter(v.items()):
                        print('field-attribute handling'+kk)
                        #if vv != None:
                        #    print('field-attribute handling'+kk+' is taken!')
                        if kk == 'type':
                            if vv in nx_type_keys:
                                fld.set('type', vv.upper())
                            #elif v in nx_base_clss or v in nx_cand_clss:
                            #    obj.set(key, nx_base_clss_string_mangling(v))
                            else:
                                print('WARNING: key: '+k+' value: '+str(v)+' is not one of predefined type keys')
                        elif kk == 'doc': #key is a documentation string specifier
                            fld.set('doc', str(vv))
                        elif kk == nx_unit_idnt:
                            fld.set('units', vv.upper())
                        elif kk[0:2] == nx_attr_idnt: #attribute of a field
                            attr = etree.SubElement(fld, 'attribute')
                            attr.set('name', kk[2:])
                            if vv != None:
                                if isinstance(vv,dict):
                                    for kkk, vvv in iter(vv.items()):
                                        if kkk == 'name':
                                            attr.set('name', vvv)
                                        elif kkk == 'doc':
                                            attr.set('doc', vvv)
                                        elif kkk == 'type':
                                            attr.set('type', vvv.upper())
                                        elif kkk == 'enumeration':
                                            xml_handle_enumeration(attr, kkk, vvv)
                                        else:
                                            raise ValueError('ERROR: '+kkk+' faced unknown situation when processing attributes of an attribute !')
                            #else: #e.g. for case like \@depends_on:
                            #    attr.set('name', kk[2:])
                            #recursive_build(attr, vv)
                        elif kk == 'exists':
                            xml_handle_exists(fld, kk, vv)
                        elif kk == 'dimensions':
                            xml_handle_dimensions(fld, kk, vv)
                        elif kk == 'enumeration':
                            xml_handle_enumeration(fld, kk, vv)
                        else:
                            raise ValueError('ERROR: '+kk+' faced unknown situation !')
                        #else:
                        #    print('field-attribute handling'+kk+' is forgotten !')
                else:
                    if k == 'type':
                        print('')
                    elif k == 'doc': #key is a documentation string specifier
                        fld.set('doc', str(v))
                    elif k == nx_unit_idnt:
                        fld.set('units', v.upper())
                    elif k[0:2] == nx_attr_idnt: #attribute of a field
                        raise ValueError('Unknown attribute of a field case coming from no dict !')
                    elif k == 'exists':
                        xml_handle_exists(fld, k, v)
                    elif k == 'dimensions':
                        raise ValueError('Unknown dimensions of a field case coming from no dict !')
                    else:
                        raise ValueError('ERROR: '+k+' faced unknown situation !')
