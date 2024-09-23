#!/bin/bash

# File patterns to check for changes (e.g., only keep commits affecting .py files)

clean_branch() {
    cd ../../nexus_definitions
    branch_name=$1
    applications=("$2")  # Treat $2-5 as space-separated list and convert to array
    base_classes=("$3")
    contributed_definitions=("$4")
    other_files=("$5")

    # Switch to the branch
    git switch "${branch_name}"

    FILES_TO_KEEP=()

    # Restore applications if not empty
    if [ ${#applications[@]} -gt 0 ]; then
        for application in "${applications[@]}"; do
            FILES_TO_KEEP+=("applications/${application}.nxdl.xml")
        done
    else
        echo "No applications to cherry-pick."
    fi

    # Restore base_classes if not empty
    if [ ${#base_classes[@]} -gt 0 ]; then
        for base_class in "${base_classes[@]}"; do
            FILES_TO_KEEP+=("base_classes/${base_class}.nxdl.xml")
        done
    else
        echo "No base classes to cherry-pick."
    fi

    # Restore contributed_definitions if not empty
    if [ ${#contributed_definitions[@]} -gt 0 ]; then
        for contributed in "${contributed_definitions[@]}"; do
            FILES_TO_KEEP+=("contributed_definitions/${contributed}.nxdl.xml")
        done
    else
        echo "No contributed definitions to cherry-pick."
    fi

    # Restore other files if not empty
    if [ ${#other_files[@]} -gt 0 ]; then
        for file in "${other_files[@]}"; do
            FILES_TO_KEEP+=("${file}")
        done
    else
        echo "No other files to cherry-pick."
    fi

    # Step 1: Identify the common ancestor commit with upstream/main
    base_commit=$(git merge-base upstream/main "${branch_name}")

    # Step 2: Create a new temporary branch for cherry-picking
    git branch -D temp-cleaned-branch || true
    git checkout -b temp-cleaned-branch "${base_commit}"
    git checkout upstream/main -- .

    # Step 3: Get a sorted list of relevant commits (by date, oldest first)
    all_commits=()

    for file in "${FILES_TO_KEEP[@]}"; do
        # Retrieve the commits for the current file
        commits=$(git log --pretty=format:"%H" "${base_commit}..${branch_name}" -- "$file")
        # Convert commits string into an array
        IFS=$'\n' read -r -d '' -a commit_array <<< "$commits"$'\n'

        # Append the commits to all_commits array
        all_commits+=("${commit_array[@]}")
    done

    unique_commits=($(printf "%s\n" "${all_commits[@]}"))

    reversed_commits=()
    for ((i=${#unique_commits[@]}-1; i>=0; i--)); do
        reversed_commits+=("${unique_commits[i]}")
    done

    # Step 4: Cherry-pick those commits that actually have the changes
    for commit in "${reversed_commits[@]}"; do
        echo $commit # >> "commits.txt"
        git cherry-pick "$commit" || {
            conflicting_files=$(git diff --name-only --diff-filter=U)
            echo "Conflict while cherry-picking commit $commit. Conflicts in the following files: $conflicting_files"

            for file in $conflicting_files; do
                echo $file
                if ! [[ ${FILES_TO_KEEP[*]} =~ $file ]]; then
                    echo "Resolving conflict in $file."
                    if git ls-tree -r upstream/main | grep -q "$file"; then
                        echo "Using state from current branch."
                        git checkout upstream/main -- $file
                    else
                        echo "File doesn't exist in the current branch. Removing file."
                        git rm -- $file
                    fi
                else
                    echo "Conflict in one of the files to be cherry-picked: $file. Please resolve manually."
                    git checkout --theirs $file
                    git add $file
                    # git cherry-pick --continue
                fi
            done
            # git commit --message "Auto-merge commit during cherry-pick resolution"
            git commit --allow-empty-message --no-edit
            }
    done

    # Step 5: Revert unintentional changes from cherry-pick
    for file in $(git diff upstream/main --name-only); do
        echo "Processing $file"
        if ! [[ ${FILES_TO_KEEP[*]} =~ $file ]]; then
            if git ls-tree -r upstream/main | grep -q "$file"; then
                git checkout upstream/main -- $file
            else
                git rm -- $file
            fi
        fi
    done    
    git commit -m "revert unintentional changes from cherry-pick"

    # Step 6: Switch back to the original branch and reset to cleaned branch
    git checkout "${branch_name}"
    git reset --hard temp-cleaned-branch
    
    # Step 7: Delete the temporary branch
    git branch -D temp-cleaned-branch

    echo "Rebase finished. Only commits affecting $FILES_TO_KEEP were kept."
}

# clean_branch fairmat-2024-nxarpes
# Pass inputs to the function
#clean_branch "$@"
applications=""
base_classes="NXsubentry" # NXsubentry NXidentifier"
contributed_definitions=""
other_files=""

clean_branch fairmat-2024-nxsubentry "$applications" "$base_classes" "$contributed_definitions" "$other_files"