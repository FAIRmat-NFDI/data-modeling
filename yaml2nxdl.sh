dirs="Base_Classes/new electron_microscopy/nexus_code_camp_2022 atomprobe_microscopy/nexus_code_camp_2022 ARPES/Application_Definitions optical_spectroscopy IV_temp XRD"
dirs_append="Base_Classes/appended"
files=`for n in $dirs; do ls $n/*.yml; ls $n/*.yaml; done`
files_append=`for n in $dirs_append; do ls $n/*.yml; ls $n/*.yaml; done`
for f in $files; do
  python -m nexusparser.tools.yaml2nxdl.yaml2nxdl --input-file $f
done
for f in $files_append; do
  python -m nexusparser.tools.yaml2nxdl.yaml2nxdl --input-file $f
done



