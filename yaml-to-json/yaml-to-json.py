#!/usr/bin/env python
""" A function that can display a dict structure in a tree-like form """

def disp_dict(d, level=0):
    """ Take a dict, and go through its keys and values, display them in a
        tabulated form.
        Run recursively for dicts inside

        @param d        dict to be displayed
        @param level    level of indentation we are at

        return: nothing
    """
    mtabs = '\u2014\u2014'*level if level > 0 else ''
    mtabs = f'{level}{mtabs}'
    tabs = '  '*level if level > 0 else ''
    tabs = f' {tabs}'

    if type(d) != dict:
        raise ValueError('Invalid input variable type!')
        return

    firstLine= True
    for k,v in d.items():
        if type(v) == dict:
            disp_dict(v, level= level+1)
        else:
            if firstLine:
                print(f'\u251C{mtabs}> {k}: ({type(v).__name__}) {v}')
                firstLine= False

            else:
                print(f'\u2502{tabs}  {k}: ({type(v).__name__}) {v}')

    if level > 0:
        print('\u2502')
    else:
        print('')
# end of disp_dict

# test it:
import pyaml as yam
import os
filepath = '../optical_spectroscopy'
with open(os.path.join(filepath, 'ellipsometry-summary.yaml')) as fp:
    ydict = yam.yaml.safe_load(fp)
    disp_dict(ydict)

# export to json:
import json
with open(os.path.join(filepath, 'ellipsometry-summary.json'), 'wt') as fp:
    json.dump(ydict, fp, sort_keys=True, indent=2)
# end writing json file
