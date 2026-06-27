# Reading data with `RASXfile``

The `RASXfile` object has three fields/methods:

- **data**: Holding the scan and intensity data.
- **\_meta**: A dict of metadata from the files. These files are dumped to json files in this repository.
- **get_RSM()**: A function to readout the reciprocal space map, this contains the intensity values + scan positions.
  This essentially combines the data and positions data.
- **positions**: Holding arrays of positions for the different scan axes.
- **images**: Seems to be empty for all example files.
