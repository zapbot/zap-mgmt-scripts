# Runs all of the scripts required to create PRs for Crowdin changes

# Assume we're running in the zap-mgmt-scripts directory

./download-i18n.sh
./commit-i18n.sh
./update-repos.sh
