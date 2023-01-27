dirs="Base_Classes/new Application_Definitions/new"
# electron_microscopy/nexus_code_camp_2022 atomprobe_microscopy/nexus_code_camp_2022 ARPES/Application_Definitions optical_spectroscopy IV_temp XRD"
dirs_append="Base_Classes/appended"
files=`for n in $dirs; do ls $n/*.yml; ls $n/*.yaml; done`
files_append=`for n in $dirs_append; do ls $n/*.yml; ls $n/*.yaml; done`
for f in $files; do
  echo "File name$f\n\n"
  python -m nexusutils.nyaml2nxdl.nyaml2nxdl --input-file $f
done
for f in $files_append; do
  echo "File name$f\n\n"
  python -m nexusutils.nyaml2nxdl.nyaml2nxdl --input-file $f
done


