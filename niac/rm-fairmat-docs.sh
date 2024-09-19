 
 
alias checkout_main='git checkout upstream/main'

make clean-nyaml
checkout_main .github/workflows 
checkout_main .gitignore
checkout_main Makefile
checkout_main common/ 
checkout_main README.md 
checkout_main dev_tools/globals/urls.py
checkout_main requirements.txt
cd manual/source
checkout_main conf.py
checkout_main _static
checkout_main examples/index.rst
rm fairmat_cover.rst
rm img/FAIRmat*
rm sed/entry-page.html
rm nexus-index.rst
rm *-structure.rst
cd ../..


# add to manual/source/conf.py
# \DeclareUnicodeCharacter{394}{$\Delta$}
# \DeclareUnicodeCharacter{2206}{$\Delta$}