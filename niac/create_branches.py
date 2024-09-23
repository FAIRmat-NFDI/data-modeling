import os
from pathlib import Path
import yaml
import subprocess

from typing import List, Literal


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
    task:Literal["create", "clean"] = "create",
    applications: List[str] = [],
    base_classes: List[str] = [],
    contributed_definitions: List[str] = [],
    other_files: List[str] = [],
):
    if task == "create":
        bash_script = "./create_branch.sh"
    elif task == "clean":
        bash_script = "./clean_branch.sh"
    else:
        raise ValueError("no script for task {task}!")

    # Prepare the applications and base_classes as space-separated strings
    applications_str = " ".join(applications)
    base_classes_str = " ".join(base_classes)
    contributed_definitions_str = " ".join(contributed_definitions)
    other_files_str = " ".join(other_files)

    # Run the bash script with arguments
    result = subprocess.run(
        [
            "bash",
            bash_script,
            branch_name,
            applications_str,
            base_classes_str,
            contributed_definitions_str,
            other_files_str,
        ],
        capture_output=True,
        text=True,
    )

    # # Print the output and error messages
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)


#### CHANGED EXISTING APPLICATIONS
changed_applications = {"NXarpes"}

for appdef in changed_applications:
    branch_name = f"fairmat-2024-{appdef.lower()}"
    run_bash_script(branch_name=branch_name, task="create", applications=[appdef])
    # run_bash_script(branch_name=branch_name, task="clean", applications=[appdef])


#### CHANGED EXISTING BASE CLASSES
changed_base_classes = {
    # git diff --name-only upstream/main base_classes/*.nxdl.xml | sed 's|base_classes/\(.*\)\.nxdl\.xml|\1|'
    "NXaperture", # PR ready
    "NXbeam", # PR ready
    "NXdata", # PR ready
    "NXdetector", # PR ready
    "NXentry", # PR ready
    "NXenvironment", # PR ready
    "NXinstrument",
    "NXmonochromator",
    "NXprocess",
    "NXroot",
    "NXsample", # PR ready
    "NXsample_component", # together with NXsample PR
    "NXsensor", # together with NXenvironment PR
    "NXsource", # PR ready
    "NXsubentry", # together with NXentry PR
    "NXtransformations",
    "NXuser",
}

for base_class in changed_base_classes:
    branch_name = f"fairmat-2024-{base_class.lower()}"
    # run_bash_script(branch_name, base_classes=[base_class])


#### common_base_classes
branch_name = f"fairmat-2024-common-base-classes"
with open(f"common_new_needed.yaml", "r") as stream:
    yml_data = yaml.safe_load(stream)
    common_base_classes = list(
        yml_data["common new base classes needed for more than one domain"].keys()
    )
    # print(f"common new base classes:\n{common_base_classes}\n")
    # run_bash_script(branch_name, base_classes=common_base_classes)

#### contributed definitions
branch_name = f"fairmat-2024-contributed"
with open(f"keep_in_contributed.yaml", "r") as stream:
    yml_data = yaml.safe_load(stream)
    contributed_classes = yml_data["keep in contributed"]
    # print(f"contributed classes:\n{contributed_classes}\n")
    # run_bash_script(branch_name, contributed_definitions=contributed_classes)

### computational geometry
branch_name = f"fairmat-2024-computational-geometry"
with open(f"computational_geometry.yaml", "r") as stream:
    yml_data = yaml.safe_load(stream)
    cg_base_classes = yml_data["new base classes"]
    # print(f"computational geometry:\n{cg_base_classes}\n")
    # run_bash_script(branch_name, base_classes=cg_base_classes)


#### Domain PRs
for domain in [
    "APM",
    "EM",
    "MPES",
    "optical_spectroscopy",
]:
    branch_name = f"fairmat-2024-{domain.lower()}"
    with open(f"{domain}.yaml", "r") as stream:
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

    applications = sorted(new_applications + updated_applications)
    base_classes = sorted(new_base_classes + updated_base_classes)

    # print(domain)
    # print(f"applications:\n\t{applications}")
    # print(f"base_classes:\n\t{base_classes}")
    # print(f"other files:\n\t{other_files}\n")

    # run_bash_script(branch_name, applications=applications, base_classes=base_classes, other_files=other_files)


#### other files
branch_name = f"fairmat-2024-dev-tools-and-manual"
with open(f"keep_in_contributed.yaml", "r") as stream:
    other_files = ["dev_tools", "manual"]
    # print(f"other files:\n{other_files}\n")
    # run_bash_script(branch_name, other_files=other_files)