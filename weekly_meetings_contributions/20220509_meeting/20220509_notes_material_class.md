
	
# Notes 09.05.2022 from weekly task force meeting	
Discussion on blocks/base classes
idea of "material" class

## Homework:
	- review draft on material class and add potential subclasses
	- indentify input in process? eg: add chemical, add precusor, material source parameters
	- material in process?

	  

'''
{	
class material:
	type = [pure chemical, compound, substrate]
	# substrates for epitaxy
	- substrate:
		- material:
			- formula: # e.g., Ga2O3
			- DOPANT:
				- element: # chem. symbol, e.g. Fe
				- concentration: # cm^-3, e.g., 3e18
		- crystal structure: # e.g., monoclinic, lattice params.??? - ideally all description a,b,c, aplha, beta, gamma
		- surface orientation: 
			- hkl: # e.g. (100)
			- offcut:
				- degrees: #, e.g. 2
				- towards:  e.g. (001)
		- vendor: # text
		- wafer id: # text
		- shape: # e.g., 2" dia, 10mm x 10mm or piece, e.g., 1/4 2" or 3mm x 5mm
		- thickness: # in mm
		- polishing: # 1sp = single sided, 2sp = double sided
	
	- Chemical (block):
  
		- Chemical name
		- CAS number
		- Purity (%)
		- Distributor
		- //Additional comment
		- //Sku number
		- Formula
		- safty data sheet
		- Amount of chemical bottle
		- opening time of chemical
		
	- what other subclasses needed?

}
'''
	

Process:
	- indentify input in process? eg: add chemical, add precusor, material source parameters
	- material in process?
		-  
		
	- chemical in process step:

	  - Timestamp
	  - //Duration of adding chemical (s)
	  - Amount (g)
	
