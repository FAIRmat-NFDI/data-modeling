#!/bin/bash
create_branch() {
  cd ../../nexus_definitions

  branch_name=$1
  applications=($2)  # Treat $2-5 as space-separated list and convert to array
  base_classes=($3)
  contributed_definitions=($4)
  other_files=($5)

  # Switch to the base branch
  git switch fairmat-2024
  
  # Create a new branch
  git checkout -b "${branch_name}"

  echo $applications
  echo $base_classes

  # List files in fairmat-2024 not in upstream/main
  files_to_remove=$(git diff --name-only upstream/main...fairmat-2024)

  # Remove those files
  if [ -n "$files_to_remove" ]; then
    echo "Removing files that are not in upstream/main:"
    echo "$files_to_remove"
    rm $files_to_remove
  fi
  
  # Now check out files from upstream/main
  git checkout upstream/main -- .
  
  # Restore applications if not empty
  if [ ${#applications[@]} -gt 0 ]; then
    for application in "${applications[@]}"; do
      git restore --source fairmat-2024 "applications/${application}.nxdl.xml"
    done
  else
    echo "No applications to restore."
  fi

  # Restore base_classes if not empty
  if [ ${#base_classes[@]} -gt 0 ]; then
    for base_class in "${base_classes[@]}"; do
      git restore --source fairmat-2024 "base_classes/${base_class}.nxdl.xml"
    done
  else
    echo "No base classes to restore."
  fi

  # Restore contributed_definitions if not empty
  if [ ${#contributed_definitions[@]} -gt 0 ]; then
    for contributed in "${contributed_definitions[@]}"; do
      git restore --source fairmat-2024 "contributed_definitions/${contributed}.nxdl.xml"
    done
  else
    echo "No contributed definition to restore."
  fi

  # Restore other files if not empty
  if [ ${#other_files[@]} -gt 0 ]; then
    for file in "${other_files[@]}"; do
      git restore --source fairmat-2024 ${file} 
    done
  else
    echo "No other files to restore."
  fi

  # Commit and push
  git add -A
  git commit -m "pull out modifications for ${branch_name}"
  # git push --set-upstream origin "${branch_name}"
  git switch fairmat-2024
  
}

# Pass inputs to the function
create_branch "$@"
