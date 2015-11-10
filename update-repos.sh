# Update all of the repos to the latest ones from zaproxy
# Requires a ~/.netrc file present with valid credentials

# Assume we're running in the zap-mgmt-scripts directory
cd ..

# zaproxy
cd zaproxy
git fetch upstream
git merge upstream/develop -m Sync
git push origin develop
cd ..

# zap-extensions
cd zap-extensions
git fetch upstream
git merge upstream/master -m Sync
git push origin master
cd ..

# zap-extensions beta
cd zap-extensions_beta
git fetch upstream
git merge upstream/beta -m Sync
git push origin beta
cd ..

# zap-extensions alpha
cd zap-extensions_alpha
git fetch upstream
git merge upstream/alpha -m Sync
git push origin alpha
cd ..
