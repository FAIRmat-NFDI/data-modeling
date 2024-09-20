cd ../../nexus_definitions 
 

# make clean-nyaml
git checkout upstream/main .github/workflows 
rm .github/workflows/fairmat*
git checkout upstream/main .gitignore
git checkout upstream/main Makefile
git checkout upstream/main common/ 
git checkout upstream/main README.md 
git checkout upstream/main dev_tools/globals/urls.py
git checkout upstream/main requirements.txt
cd manual/source
git checkout upstream/main conf.py
git checkout upstream/main index.rst
git checkout upstream/main examples/index.rst
rm _static/blockquote.css.bak
rm _static/to_alabaster.css
rm _static/to_rtd.css
rm fairmat-cover.rst
rm img/FAIRmat*
rm sed/entry-page.html
rm nexus-index.rst
rm *-structure.rst
cd ../..