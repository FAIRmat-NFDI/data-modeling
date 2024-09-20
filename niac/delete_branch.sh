delete_branch () {
  cd ../../nexus_definitions
  branch_name=$1 
  git restore --staged .
  git restore .
  git clean -f
  git switch fairmat-2024
  git branch -D "${branch_name}"
}

branch_name="fairmat-2024-mpes"
delete_branch "$branch_name" 