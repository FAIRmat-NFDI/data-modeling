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
all_new_base_classes = set()
common_new_base_classes = {}
new_base_classes = {}


for technique, contributed_appdefs in appdef_map.items():
    yml_data = {technique: {}}
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
    all_new_base_classes.update(contributed_base)
    new_base_classes[technique] = contributed_base

    # Print affected/used classes
    if PRINT_CLASSES:
        print(f"{technique}")
        print("  appdefs:")
        print_str_list(sorted(contributed_appdefs))
        print("  unchanged existing base classes:")
        print_str_list(sorted(unchanged_existing_base))
        print("  changed existing base classes:")
        print_str_list(sorted(changed_existing_base))
        print("  contributed classes:")
        print_str_list(sorted(contributed_base))

    # Automatically write yaml file
    if technique == "MPES":
        yml_data[technique]["depends on changes in these applications"] = ["NXarpes"]
    else:
        yml_data[technique]["depends on changes in these applications"] = ["none"]
    yml_data[technique]["depends on unchanged base_classes"] = sorted(
        unchanged_existing_base
    )
    yml_data[technique]["depends on changes in these base_classes"] = sorted(
        changed_existing_base
    )
    yml_data[technique]["move to applications"] = sorted(contributed_appdefs)
    yml_data[technique]["move to base_classes"] = sorted(contributed_base)

    # Path to the output YAML file
    yml_file = f"{technique}.yaml"

    # Write the data to the YAML file
    with open(yml_file, "w") as file:
        yaml.dump(yml_data, file, sort_keys=False)

# contributed = {c for c in contributed if c != appdef}

for technique, base_class_set in new_base_classes.items():
    for base_class in base_class_set:
        try:
            common_new_base_classes[base_class] += [technique]
        except KeyError:
            common_new_base_classes[base_class] = [technique]

common_new_base_classes = {
    k: v for k, v in common_new_base_classes.items() if len(v) > 1
}

if PRINT_CLASSES:
    print("all contributed appdefs:")
    print_str_list(sorted(all_contributed_appdefs))
    print("all new base classes needed for our techniques:")
    print_str_list(sorted(all_new_base_classes))
    print("common new base classes needed for our techniques:")
    print_str_list(sorted(common_new_base_classes))

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


yml_config = {
    "all_new_needed": {
        "all new base classes needed for our techniques": sorted(all_new_base_classes)
    },
    "common_new_needed": {
        "common new base classes needed for our techniques": common_new_base_classes
    },
    "keep_in_contributed": {
        "keep_in_contributed": sorted(keep_in_contributed),
    },
}

for file_name, yml_data in yml_config.items():
    yml_file = f"{file_name}.yaml"
with open(yml_file, "w") as file:
    yaml.dump(yml_data, file, sort_keys=False)


##
def move_files(classes: List[str], target: Literal["application", "base_classes"]):
    contributed_folder = str(Path(*(NEXUS_REPO_FOLDER, "contributed_definitions")))

    for class_name in sorted(classes):
        nxdl_file = Path(*(contributed_folder, f"{class_name}.nxdl.xml"))
        nyaml_file = Path(*(contributed_folder, "nyaml", f"{class_name}.yaml"))

        for old_file in [nxdl_file, nyaml_file]:
            target_file = str(old_file).replace("contributed_definitions", target)

            shutil.move(old_file, target_file)

move_files(all_new_base_classes, "base_classes")
move_files(all_contributed_appdefs, "applications")
