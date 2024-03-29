
```yaml
symbols:
	N_parameters: The number of parameters which got scanned.
(NXmeasurement):
	scan_names(NX_CHAR):
		doc: Names of the scanned values
		# enumeration: In an appdef this should be further specified with an 
		#			   enumeration, i.e. which scans are allowed.
		dimensions:
			rank: 1
			dim: [[1, N_parameters]]
	scan_indices(NX_NUMBER):
		doc: |
			An relation to which data index the data at a certain array
			position belongs.
		dimensions:
			rank: 1
			dim: [[1, N_parameters]]
	scan_length(NX_NUMBER):
		doc: The length of a scan axis
		dimensions:
			rank: 1
			dim: [[1, N_parameters]]
	scan_unit(NX_CHAR):
		doc: The unit of a scan axis
		dimensions:
			rank: 1
			dim: [[1, N_parameters]]
	scan_values(NX_CHAR):
		doc: Description of the scanned values
		dimensions:
			rank: N_parameters
	alternate_axis_SCANNAME(NX_NUMBER):
		original_entry(NX_CHAR):
			doc: Pointer to where the original measurement data is stored.
		derived_from(NX_CHAR):
			doc: A pointer to the axis this alternate axis is derived from.
		dimensions:
			rank: 1
			dim: [[1, scan_length[N]]]
	# axisN has to exist for every value of scan_names
	axis_SCANNAME(NX_NUMBER):
	    doc: |
		    The scan axis values. This should contain actually measured values.
		    If you want to store set parameters as well please use the
		    alternate_axis field.
		original_entry(NX_CHAR):
			doc: Pointer to where the original measurement data is stored.
		dimensions:
			rank: 1
			dim: [[1, scan_length[N]]]
	signal(NX_NUMBER):
		original_entry(NX_CHAR):
			doc: Pointer to where the original measurement data is stored.
		dimensions:
			rank: N_parameters
			dim: [[1, scan_length1], [2, scan_length2], ...]]
```

The major missing part is how do we dynamically link the length of the scans to the dimensionality of the data. Otherwise it should work this way and be able to represent any form of measurement-scan combination.

#area-b #nexus #general-patterns 