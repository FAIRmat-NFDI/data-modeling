#!/usr/bin/env python
""" the quick an dirty loading of the data table.
"""
import numpy as nu
from matplotlib import pyplot as pl
import sys

with  open('../../190801_Si_SiO2_2nm_test/190801_Si_SiO2_2nm_test_mat.txt') as fp:
    txt = fp.readlines()
    fp.close()

# last character is the new line:
head = txt[0][:-1].split('\t')
ncol = len(head)
print('Found:', ncol, 'columns in header')

dat = [i[:-1].split('\t') for i in txt[1:]]
result = nu.asarray(dat, dtype='f')

# how many rows?
# data are put after each other, but the first column
# is an incremented X
rmin = result[:,0].min()
indx = (result[:,0] == rmin).nonzero()[0]
if len(indx) == 0:
    print('No valid X-data found!')
    sys.exit(1)

nrow = indx[1]-indx[0] # assuming all have the same length
ndat = len(indx)
result.shape = (ndat, nrow, ncol)

pl.clf()
# we have to scale to the full plot:
pl.ylim(result[:,:,6].min(), result[:,:,6].max())
pl.xlabel(head[0])
pl.ylabel(head[6])

for i in range(ndat):
    pl.plot(result[i,:,0], result[i,:,6], '-')
