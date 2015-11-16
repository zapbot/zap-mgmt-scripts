# Update all of the repos to the latest ones from zaproxy
# Requires a ~/.netrc file present with valid credentials

git config --global user.name "zapbot"
git config --global user.email "zapbot@zaproxy.org"

# Assume we're running in the zap-mgmt-scripts directory
cd ..

# zaproxy
cd zaproxy
git fetch upstream
git checkout -B develop upstream/develop
git push origin develop --force
cd ..

# zap-extensions
cd zap-extensions
git fetch upstream
git checkout -B master upstream/master
git push origin master --force
cd ..

# zap-extensions beta
cd zap-extensions_beta
git fetch upstream
git checkout -B beta upstream/beta
git push origin beta --force
cd ..

# zap-extensions alpha
cd zap-extensions_alpha
git fetch upstream
git checkout -B alpha upstream/alpha
git push origin alpha --force
cd ..
