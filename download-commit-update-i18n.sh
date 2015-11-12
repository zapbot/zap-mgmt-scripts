# Runs all of the scripts required to create PRs for Crowdin changes

# Assume we're running in the zap-mgmt-scripts directory

./update-repos.sh
./download-i18n.sh
./commit-i18n.sh
