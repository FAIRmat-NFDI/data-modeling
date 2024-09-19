import os
from typing import List, Literal
from pathlib import Path
import xml.etree.ElementTree as ET
import yaml
import shutil

PRINT_CLASSES = True

current_path = Path(__file__).resolve()

# Find "data-modeling" in the path and split at that level
for parent in current_path.parents:
    if parent.name == "data-modeling":
        data_modeling_path = parent
        break

NEXUS_REPO_FOLDER = Path(*(data_modeling_path.parent, "nexus_definitions"))

def extract_all_classes(xml_file: str, visited_files=None) -> (set, set):
    """
    Recursively extracts all unique 'type' attributes from <group> elements in the given XML file
    and any other files that are linked through groups.

    Args:
        xml_file (str): Path to the XML file.
        visited_files (set): Set of visited files to prevent redundant processing.

    Returns:
        tuple: Two sets, (contributed, base), with the groups found in contributed and base directories respectively.
    """
    if visited_files is None:
        visited_files = set()

    # If the file has already been processed, return empty sets
    if xml_file in visited_files:
        return set(), set()

    # Mark the current file as visited
    visited_files.add(xml_file)

    # Parse the XML file
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Namespace dictionary (extract the relevant namespace from the root element)
    namespaces = {"nx": "http://definition.nexusformat.org/nxdl/3.1"}

    # Create sets to store unique 'type' attributes
    contributed = set()
    base = set()

    # Find all <group> elements (including subgroups) and retrieve the 'type' attribute
    classes = [group.get("type") for group in root.findall(".//nx:group", namespaces)]
    
     # Check if the <definition> tag has an 'extends' attribute and add it if it's not 'NXobject'
    extends_attr = root.get("extends")
    if extends_attr and extends_attr != "NXobject":
        classes += [extends_attr]

    cls_name = "NXem_method"
    
    for class_name in classes:
        if class_name:
            # Check for the file in base_classes directory first
            new_xml_file = Path(NEXUS_REPO_FOLDER, "base_classes", f"{class_name}.nxdl.xml")
            if new_xml_file.exists():
                # Recursively process the file and add to base set
                new_contrib, new_base = extract_all_classes(new_xml_file, visited_files)
                contributed.update(new_contrib)
                base.update(new_base)
                base.add(class_name)
            else:
                # Check for the file in contributed_definitions directory
                new_xml_file = Path(
                    NEXUS_REPO_FOLDER, "contributed_definitions", f"{class_name}.nxdl.xml"
                )

                if new_xml_file.exists():
                    new_contrib, new_base = extract_all_classes(
                        new_xml_file, visited_files
                    )
                    contributed.update(new_contrib)
                    base.update(new_base)
                    contributed.add(class_name)

    return contributed, base


changed_base_classes = {
    # git diff --name-only upstream/main base_classes/*.nxdl.xml | sed 's|base_classes/\(.*\)\.nxdl\.xml|\1|'
    "NXaperture",
    "NXbeam",
    "NXdata",
    "NXdetector",
    "NXentry",
    "NXenvironment",
    "NXinstrument",
    "NXmonochromator",
    "NXprocess",
    "NXroot",
    "NXsample",
    "NXsample_component",
    "NXsensor",
    "NXsource",
    "NXsubentry",
    "NXtransformations",
    "NXuser",
}

appdef_map = {
    "APM": ["NXapm"],
    "EM": ["NXem"],
    "MPES": ["NXmpes", "NXmpes_arpes", "NXxps"],
    "optical_spectroscopy": ["NXoptical_spectroscopy", "NXellipsometry", "NXraman"],
}


def print_str_list(strings: list):
    for s in strings:
        print(f"    {s}")
    print("\n")

all_contributed_appdefs = set()
  
empty_dict = {k: {} for k in list(appdef_map.keys())}

classes = {
    "new application definitions": empty_dict.copy(),
    "new base classes only introduced in this domain": empty_dict.copy(),
    "all new base classes": empty_dict.copy(),
    "depends on changes in these base_classes": empty_dict.copy(),
    "depends on changes in these applications": empty_dict.copy(),
    "depends on unchanged base_classes": empty_dict.copy(),
    # "all new base classes needed for our techniques": [],
    # "common new base classes needed for more than one domain": [],
    # "keep in contributed": []
}

for domain, contributed_appdefs in appdef_map.items():   
    all_existing_base = set()
    contributed_base = set()
    for appdef in contributed_appdefs:
        all_contributed_appdefs.update([appdef])
        xml_file = Path(*(NEXUS_REPO_FOLDER, "contributed_definitions", f"{appdef}.nxdl.xml"))
        contributed, base = extract_all_classes(xml_file)
        all_existing_base.update(base)
        contributed_base.update(contributed)
    
    contributed_base = {c for c in contributed_base if c not in contributed_appdefs}

    changed_existing_base = {
        base for base in all_existing_base if base in changed_base_classes
    }
    unchanged_existing_base = {
        base for base in all_existing_base if base not in changed_base_classes
    }
   
    classes["new application definitions"][domain] = sorted(contributed_appdefs)
    classes["all new base classes"][domain] = sorted(contributed_base)
    classes["depends on changes in these base_classes"][domain] = sorted(
        changed_existing_base
    )
    # Automatically write yaml file
    if domain == "MPES":
        classes["depends on changes in these applications"][domain] = ["NXarpes"]
    else:
        classes["depends on changes in these applications"][domain] = ["none"]
    
    classes["depends on unchanged base_classes"][domain] = sorted(
        unchanged_existing_base
    )
all_new_base_classes = sorted(set.union(*map(set, classes["all new base classes"].values())))

common_new_base_classes = {}

for domain in appdef_map.keys():
    base_class_set = classes["all new base classes"][domain]
    for base_class in base_class_set:
        try:
            common_new_base_classes[base_class] += [domain]
        except KeyError:
            common_new_base_classes[base_class] = [domain]

common_new_base_classes = {
    k: v for k, v in common_new_base_classes.items() if len(v) > 1
}

for domain in appdef_map.keys():
    new_base_classes_domain = classes["all new base classes"][domain]
    difference = list(set(new_base_classes_domain) - set(list(common_new_base_classes.keys())))
    classes["new base classes only introduced in this domain"][domain] = difference

all_contributed = file_names = [
    f.split(".nxdl.xml")[0]
    for f in os.listdir(Path(*(NEXUS_REPO_FOLDER, "contributed_definitions")))
    if f.endswith(".nxdl.xml")
]
keep_in_contributed = [
    file
    for file in all_contributed
    if file not in all_new_base_classes and file not in all_contributed_appdefs
]

#####################################################
# Write YAML files
#####################################################
for domain, contributed_appdefs in appdef_map.items():
    yml_data = {}

    if PRINT_CLASSES:
        print(f"{domain}")
        print("  appdefs:")
        print_str_list(sorted(contributed_appdefs))

    for key, cls_dict in classes.items():
        yml_data[key] = sorted(cls_dict[domain])
        if PRINT_CLASSES:
             print(f"  {key}")
             print_str_list(sorted(cls_dict[domain]))

    yml_file = f"{domain}.yaml"

    # Write the data to the YAML file
    with open(yml_file, "w") as file:
        yaml.dump(yml_data, file, sort_keys=False)
    
yml_config = {
    "all_new_needed": {
        "all new base classes needed for our techniques": sorted(all_new_base_classes)
    },
    "common_new_needed": {
        "common new base classes needed for more than one domain": dict(sorted(common_new_base_classes.items()))
    },
    "keep_in_contributed": {
        "keep in contributed": sorted(keep_in_contributed),
    },
}

for file_name, yml_data in yml_config.items():
    yml_file = f"{file_name}.yaml"
    with open(yml_file, "w") as file:
        yaml.dump(yml_data, file, sort_keys=False)

if PRINT_CLASSES:
    print("all contributed appdefs:")
    print_str_list(sorted(all_contributed_appdefs))
    print("all new base classes needed for our techniques:")
    print_str_list(sorted(all_new_base_classes))
    print("common new base classes needed for more than one domain:")
    print_str_list(sorted(common_new_base_classes))
    print("keep in contributed:")
    print_str_list(sorted(keep_in_contributed))




#####################################################
# MOVING OF FILES
#####################################################
CONTRIBUTED_FOLDER = str(Path(*(NEXUS_REPO_FOLDER, "contributed_definitions")))
FOLDERS_TO_MOVE = [
    ("xps", "applications")
]

additional_base_classes_to_add = [
    "NXcs_"
]

MOVE_FILES = False

def move_classes(classes: List[str], target: Literal["application", "base_classes"]):
    for class_name in sorted(classes):
        nxdl_file = Path(*(CONTRIBUTED_FOLDER, f"{class_name}.nxdl.xml"))
        nyaml_file = Path(*(CONTRIBUTED_FOLDER, "nyaml", f"{class_name}.yaml"))

        for old_file in [nxdl_file, nyaml_file]:
            target_file = str(old_file).replace("contributed_definitions", target)

            try:
                shutil.move(old_file, target_file)
            except FileNotFoundError as exc:
                print(exc)

if MOVE_FILES:
    move_classes(all_new_base_classes, "base_classes")
    move_classes(all_contributed_appdefs, "applications")
    move_classes(additional_base_classes_to_add, "base_classes")

    for (folder, target) in FOLDERS_TO_MOVE:
        old_path = Path(*(CONTRIBUTED_FOLDER, folder))
        target_file = str(old_path).replace("contributed_definitions", target)
        shutil.move(old_path, target_file)