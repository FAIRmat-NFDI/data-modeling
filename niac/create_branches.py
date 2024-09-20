import os
from pathlib import Path
import yaml
import subprocess

from typing import List


PRINT_CLASSES = True

current_path = Path(__file__).resolve()

# Find "data-modeling" in the path and split at that level
for parent in current_path.parents:
    if parent.name == "data-modeling":
        data_modeling_path = parent
        break

NEXUS_REPO_FOLDER = Path(*(data_modeling_path.parent, "nexus_definitions"))


def run_bash_script(
    branch_name: str,
    applications: List[str] = [],
    base_classes: List[str] = [],
    contributed_definitions: List[str] = [],
    other_files: List[str] = []
):
    bash_script = "./create_branch.sh"

    # Prepare the applications and base_classes as space-separated strings
    applications_str = ' '.join(applications)
    base_classes_str = ' '.join(base_classes)
    contributed_definitions_str = ' '.join(contributed_definitions)
    other_files_str = ' '.join(other_files)

    # Run the bash script with arguments
    result = subprocess.run(
        ["bash", bash_script, branch_name, applications_str, base_classes_str],
        capture_output=True,
        text=True
    )

    # # Print the output and error messages
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)

#### CHANGED EXISTING APPLICATIONS
changed_applications = {"NXarpes"}

for appdef in changed_applications:
    branch_name = f"fairmat-2024-{appdef.lower()}"
    applications = [appdef]
    # run_bash_script(branch_name, applications=applications)


#### CHANGED EXISTING BASE CLASSES
changed_base_classes = {
    # git diff --name-only upstream/main base_classes/*.nxdl.xml | sed 's|base_classes/\(.*\)\.nxdl\.xml|\1|'
    "NXaperture",
    "NXbeam",
    # "NXdata",
    # "NXdetector",
    # "NXentry",
    # "NXenvironment",
    # "NXinstrument",
    # "NXmonochromator",
    # "NXprocess",
    # "NXroot",
    # "NXsample",
    # "NXsample_component",
    # "NXsensor",
    # "NXsource",
    # "NXsubentry",
    # "NXtransformations",
    # "NXuser",
}

for base_class in changed_base_classes:
    branch_name = f"fairmat-2024-{base_class.lower()}"
    base_classes = [base_class]
    # run_bash_script(branch_name, base_classes=base_classes)


#### common_base_classes
branch_name = f"fairmat-2024-common-base-classes"
with open(f"common_new_needed.yaml", 'r') as stream:
    yml_data = yaml.safe_load(stream)
    common_base_classes = list(yml_data["common new base classes needed for more than one domain"].keys())
    print(common_base_classes)

    # run_bash_script(branch_name, base_classes=common_base_classes)

#### contributed definitions
branch_name = f"fairmat-2024-contributed"
with open(f"keep_in_contributed.yaml", 'r') as stream:
    yml_data = yaml.safe_load(stream)
    contributed_classes = yml_data["keep in contributed"]
    print(contributed_classes)
    # run_bash_script(branch_name, contributed_definitions=contributed_classes)

### computational geometry
branch_name = f"fairmat-2024-computational-geometry"
with open(f"computational_geometry.yaml", 'r') as stream:
    yml_data = yaml.safe_load(stream)
    base_classes = yml_data["new base classes"]
    print(base_classes)
    # run_bash_script(branch_name, base_classes=base_classes)




#### Domain PRs
for domain in [
#    "APM",
#    "EM",
    "MPES",
   "optical_spectroscopy"
]:
    branch_name = f"fairmat-2024-{domain.lower()}"
    with open(f"{domain}.yaml", 'r') as stream:
        yml_data = yaml.safe_load(stream)

    new_applications = yml_data["new application definitions"]
    updated_applications = yml_data["depends on changes in these applications"]
    try:
        updated_applications.remove("none")
    except ValueError:
        pass
    new_base_classes = yml_data["all new base classes that this domain depends on"]
    updated_base_classes = yml_data["depends on changes in these base_classes"]

    other_files = ["applications/xps"] if domain == "MPES" else []

    # print(domain)
    # print(new_applications)
    # print(updated_applications)
    # print(new_base_classes)
    # print(updated_base_classes)

    applications = sorted(new_applications + updated_applications)
    base_classes = sorted(new_base_classes + updated_base_classes)

    print(applications)
    print(base_classes)
    print(other_files)

    # run_bash_script(branch_name, applications=applications, base_classes=base_classes, other_files=other_files)


#### other files
branch_name = f"fairmat-2024-dev-tools-and-manual"
with open(f"keep_in_contributed.yaml", 'r') as stream:
    other_files = [
        "dev_tools",
        "manual"
    ]
    print(contributed_classes)
    # run_bash_script(branch_name, contributed_definitions=contributed_classes)





# classes = {
#     "new application definitions": empty_dict.copy(),
#     "new base classes only introduced in this domain": empty_dict.copy(),
#     "all new base classes that this domain depends on": empty_dict.copy(),
#     "depends on changes in these base_classes": empty_dict.copy(),
#     "depends on changes in these applications": empty_dict.copy(),
#     "depends on unchanged base_classes": empty_dict.copy(),
#     # "all new base classes needed for our techniques": [],
#     # "common new base classes needed for more than one domain": [],
#     # "keep in contributed": []
# }

# all_contributed_appdefs = set()

# for domain, contributed_appdefs in appdef_map.items():   
#     all_existing_base = set()
#     contributed_base = set()
#     for appdef in contributed_appdefs:
#         all_contributed_appdefs.update([appdef])
#         xml_file = Path(*(NEXUS_REPO_FOLDER, "contributed_definitions", f"{appdef}.nxdl.xml"))
#         contributed, base = extract_all_classes(xml_file)
#         all_existing_base.update(base)
#         contributed_base.update(contributed)
    
#     contributed_base.update(additional_base_classes_per_domain[domain])

#     contributed_base = {c for c in contributed_base if c not in contributed_appdefs}

#     changed_existing_base = {
#         base for base in all_existing_base if base in changed_base_classes
#     }
#     unchanged_existing_base = {
#         base for base in all_existing_base if base not in changed_base_classes
#     }
   
#     classes["new application definitions"][domain] = sorted(contributed_appdefs)
#     classes["all new base classes that this domain depends on"][domain] = sorted(contributed_base)
#     classes["depends on changes in these base_classes"][domain] = sorted(
#         changed_existing_base
#     )
#     # Automatically write yaml file
#     if domain == "MPES":
#         classes["depends on changes in these applications"][domain] = ["NXarpes"]
#     else:
#         classes["depends on changes in these applications"][domain] = ["none"]
    
#     classes["depends on unchanged base_classes"][domain] = sorted(
#         unchanged_existing_base
#     )
# all_new_base_classes = sorted(set.union(*map(set, classes["all new base classes that this domain depends on"].values())))

# common_new_base_classes = {}

# for domain in appdef_map.keys():
#     base_class_set = classes["all new base classes that this domain depends on"][domain]
#     for base_class in base_class_set:
#         try:
#             common_new_base_classes[base_class] += [domain]
#         except KeyError:
#             common_new_base_classes[base_class] = [domain]

# common_new_base_classes = {
#     k: v for k, v in common_new_base_classes.items() if len(v) > 1
# }

# for domain in appdef_map.keys():
#     new_base_classes_domain = classes["all new base classes that this domain depends on"][domain]
#     difference = list(set(new_base_classes_domain) - set(list(common_new_base_classes.keys())))
#     classes["new base classes only introduced in this domain"][domain] = difference

# all_contributed = file_names = [
#     f.split(".nxdl.xml")[0]
#     for f in os.listdir(Path(*(NEXUS_REPO_FOLDER, "contributed_definitions")))
#     if f.endswith(".nxdl.xml")
# ]

# #####################################################
# # Write YAML files
# #####################################################
# for domain, contributed_appdefs in appdef_map.items():
#     yml_data = {}

#     if PRINT_CLASSES:
#         print(f"{domain}")
#         print("  appdefs:")
#         print_str_list(sorted(contributed_appdefs))

#     for key, cls_dict in classes.items():
#         yml_data[key] = sorted(cls_dict[domain])
#         if PRINT_CLASSES:
#              print(f"  {key}")
#              print_str_list(sorted(cls_dict[domain]))

#     yml_file = f"{domain}.yaml"

#     # Write the data to the YAML file
#     with open(yml_file, "w") as file:
#         yaml.dump(yml_data, file, sort_keys=False)

# additional_base_classes = {
#     "computational_geometry" : [
#         "NXcg_alpha_complex",
#         "NXcg_cylinder_set",
#         "NXcg_ellipsoid_set",
#         "NXcg_face_list_data_structure",
#         "NXcg_geodesic_mesh",
#         "NXcg_grid",
#         "NXcg_half_edge_data_structure",
#         "NXcg_hexahedron_set",
#         "NXcg_marching_cubes",
#         "NXcg_parallelogram_set",
#         "NXcg_point_set",
#         "NXcg_polygon_set",
#         "NXcg_polyhedron_set",
#         "NXcg_polyline_set",
#         "NXcg_primitive_set",
#         "NXcg_roi_set",
#         "NXcg_sphere_set",
#         "NXcg_tetrahedron_set",
#         "NXcg_triangle_set",
#         "NXcg_triangulated_surface_mesh",
#         "NXcg_unit_normal_set",
#     ]
# }

# keep_in_contributed = [
#     file
#     for file in all_contributed
#     if file not in all_new_base_classes 
#     and file not in all_contributed_appdefs
#     and not any(file in lst for lst in additional_base_classes.values())
#     # and file not in list(additional_base_classes.items())
# ]

# yml_config = {
#     "all_new_needed": {
#         "all new base classes needed for our techniques": sorted(all_new_base_classes)
#     },
#     "common_new_needed": {
#         "common new base classes needed for more than one domain": dict(sorted(common_new_base_classes.items()))
#     },
#     "keep_in_contributed": {
#         "keep in contributed": sorted(keep_in_contributed),
#     },
# }

# for key, values in additional_base_classes.items():
#     yml_config[key] = {"new base classes": sorted(set(values))}

# for file_name, yml_data in yml_config.items():
#     yml_file = f"{file_name}.yaml"
#     with open(yml_file, "w") as file:
#         yaml.dump(yml_data, file, sort_keys=False)

# if PRINT_CLASSES:
#     print("all contributed appdefs:")
#     print_str_list(sorted(all_contributed_appdefs))
#     print("all new base classes needed for our techniques:")
#     print_str_list(sorted(all_new_base_classes))
#     print("common new base classes needed for more than one domain:")
#     print_str_list(sorted(common_new_base_classes))
#     print("keep in contributed:")
#     print_str_list(sorted(keep_in_contributed))




# #####################################################
# # MOVING OF FILES
# #####################################################
# CONTRIBUTED_FOLDER = str(Path(*(NEXUS_REPO_FOLDER, "contributed_definitions")))
# FOLDERS_TO_MOVE = [
#     ("xps", "applications")
# ]

# MOVE_FILES = True

# def move_classes(classes: List[str], target: Literal["application", "base_classes"]):
#     for class_name in sorted(classes):
#         nxdl_file = Path(*(CONTRIBUTED_FOLDER, f"{class_name}.nxdl.xml"))
#         nyaml_file = Path(*(CONTRIBUTED_FOLDER, "nyaml", f"{class_name}.yaml"))

#         for old_file in [nxdl_file, nyaml_file]:
#             target_file = str(old_file).replace("contributed_definitions", target)

#             try:
#                 shutil.move(old_file, target_file)
#             except FileNotFoundError as exc:
#                 print(exc)

# if MOVE_FILES:
#     move_classes(all_new_base_classes, "base_classes")
#     move_classes(all_contributed_appdefs, "applications")
#     for cls_list in additional_base_classes.values():
#         move_classes(cls_list, "base_classes")

#     for (folder, target) in FOLDERS_TO_MOVE:
#         old_path = Path(*(CONTRIBUTED_FOLDER, folder))
#         target_file = str(old_path).replace("contributed_definitions", target)
#         shutil.move(old_path, target_file)