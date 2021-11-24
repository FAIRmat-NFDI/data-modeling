#!/usr/bin/env python3

import read_nexus
from lxml import objectify


# example path that the function will accept as a parameter
example_path = 'NXem_base_draft.yml:/ENTRY/SUBENTRY/thumbnail/mime_type'
print(example_path.split('/'))

def nxdl_to_attr_obj(nxdlPath, nexusDefPath):
    """
    Finds the path entry in NXDL file
    Grabs all the attrs in NXDL entry
    Checks Nexus base application defs for missing attrs and adds them as well
    returns attr as a Python obj that can be directly placed into the h5py library
    """
    nxdef = nxdlPath.split(':')[0]
    #nexusDefPath = os.environ['NEXUS_DEF_PATH']
    root = objectify.parse(nexusDefPath + "/applications/" + nxdef + ".nxdl.xml")
    elem = root.getroot()
    path = nxdlPath.split(':')[1]
    for group in path.split('/')[1:]:
        elem = read_nexus.get_nxdl_child(elem, group)
    return elem


result = nxdl_to_attr_obj(example_path, '/home/aman/definitions/')
print(result.attrib)