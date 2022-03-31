#!/bin/bash

apm_ymls="NXapm NXchamber NXion NXpeak NXpulser_apm NXpump NXreflectron NXstage_lab"
cd atomprobe_microscopy
for yml in $apm_ymls; do
	echo $yml
	python3 ../yaml2nxdl.py --input-file $yml.yml
done
cd ../

em_ymls="NXcorrector_cs NXem_nion NXfib NXlens_em NXscanbox_em"
cd electron_microscopy
for yml in $em_ymls; do
	echo $yml
	python3 ../yaml2nxdl.py --input-file $yml.yml
done
cd ../
