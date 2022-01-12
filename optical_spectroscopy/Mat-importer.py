""" an generic importer for ellipsometry files exported in complex text tables.
"""
import pyaml as yaml
import os
import sys
from numpy import asarray, unique, compress
from matplotlib import pyplot as pl
import pandas as pd

default_header = {'sep': '\t', 'skip': 0}

def load_header(filename, default= default_header):
    """ load the yaml description file, and apply defaults as well
        Parameters:
        filename:           a yaml file containing the definitions
        default_header:     predefined default values
    """
    with open(filename, 'rt') as fp:
        header = yaml.yaml.safe_load(fp)

    for k, v in default.items():
        if k not in header:
            header[k] = v

    return header
# end load_header

def load_as_blocks(filename, header):
    """ load a CSV output file using the header dict
    """
    if 'colnames' not in header or\
        'skip' not in header or\
        'sep' not in header:
            raise ValueError('colnames, skip and sep are required header parameters!')

    if not os.path.isfile(fn):
        raise IOError(f'File not found error: {fn}')

    data = pd.read_csv(
            fn,
            # use header = None and names to define custom column names
            header = None,
            names= header['colnames'],
            skiprows= header['skip'],
            delimiter = header['sep']
            )

    # if our table has a block structure, we hav to
    # handle it in a special way
    dt = data.to_numpy()
    keylist = []
    if 'blocks' in header:
        for head in header['blocks']:
            print('analyzing:', head)
            print('current shape:', dt.shape)
            icol = (data.columns == head).nonzero()[0][0]
            searcharray = dt.take(icol, axis=len(dt.shape)-1)
            while (len(searcharray.shape) > 1):
                searcharray = searcharray.take(0, axis=0)

            bkeys = data[head].unique()
            lens = [(searcharray == i).sum() for i in bkeys]
            print(lens)

            if (lens == lens[0]).all():
                newshape = list(dt.shape)
                print('new dimension:', lens[0])
                #dt.shape = (lens[0], int(dt.shape[0]/lens[0]), dt.shape[1])
                i = newshape.index(max(newshape))
                newshape[i] = lens[0]
                newshape.insert(i, int(dt.shape[i]/lens[0]))
                dt.shape = tuple(newshape)
                # dt.shape = (int(dt.shape[0]/lens[0]), lens[0], dt.shape[1])
                keylist.append(bkeys)

    return { 'data': dt, 'keys': keylist}
# end of load_as_blocks

def array_to_dict(data, along=0):
    """ separate a data table into sub-tables along column 'along'

        Generate unique values from the column in data[:,along],  and put every
        uniqe table piece into a dict, where the keys are the unique
        values in column.

        Parameters:
        data:   a 2D numpy array to be split up
        along:  the index of the column to use for splitting up

        Return:
        a dict containing the array slices
    """
    if len(data.shape) < 2:
        raise ValueError('data should have at least 2 dimensions!')

    if data.shape[1] <= along:
        raise ValueError('Invalid column requested!')

    # pick the column, igore the other dimensions:
    searcharray = data.take(along, axis= 1)

    # reduce the search array to a 1D array:
    while (len(searcharray.shape) > 1):
        searcharray = searcharray.take(0, axis=0)

    # find the unique values within
    uvalues = unique(searcharray)

    # collect the results
    res = {}
    for i in uvalues:
        indx = (searcharray == i)
        res[i] = data.compress(indx, axis= 0)

    return res
# end of array_to_dict

def load_as_dict(filename, header):
    """ load a CSV output file using the header dict
        separating the block parts into a dict
    """
    if 'colnames' not in header or\
        'skip' not in header or\
        'sep' not in header:
            raise ValueError('colnames, skip and sep are required header parameters!')

    if not os.path.isfile(fn):
        raise IOError(f'File not found error: {fn}')

    data = pd.read_csv(
            fn,
            # use header = None and names to define custom column names
            header = None,
            names= header['colnames'],
            skiprows= header['skip'],
            delimiter = header['sep']
            )

    # if our table has a block structure, we hav to
    # handle it in a special way
    dt = data.to_numpy()
    keylist = []
    res = {}
    if 'blocks' in header:
        for head in header['blocks']:
            print('analyzing:', head)
            print('current shape:', dt.shape)
            icol = (data.columns == head).nonzero()[0][0]
            if len(res) < 1:
                res = array_to_dict(dt, icol)
            else:
                keys = list(res.keys())
                for k in keys:
                    t = res.pop(k)
                    r_collect= array_to_dict(t, icol)
                    # we have to make combined keys for uniqueness
                    for i in r_collect:
                        res[f'{k}.{i}'] = r_collect[i]
    # end sorting out blocks

    return res
# end of load_as_dict

# test
header = load_header('2020-09-11-test.yaml')
fn = header['filename']
table = load_as_blocks(fn, header)
tableB = load_as_dict(fn, header)
