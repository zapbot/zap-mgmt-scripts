# Init all of the required repos
# Requires a ~/.netrc file present with valid credentials

# Assume we're running in the zap-mgmt-scripts directory
cd ..

# Clone the repos we dont need to update

# Clone forks of the repos we need to update
# and update the to sync with the originals
# change zapbot to your user if required

# zap-admin
git clone https://github.com/zapbot/zap-admin.git
cd zap-admin
git remote add upstream https://github.com/zaproxy/zap-admin.git
cd ..

# zaproxy
git clone https://github.com/zapbot/zaproxy.git
cd zaproxy
git remote add upstream https://github.com/zaproxy/zaproxy.git
cd ..

# zap-extensions
git clone https://github.com/zapbot/zap-extensions.git
cd zap-extensions
git remote add upstream https://github.com/zaproxy/zap-extensions.git
cd ..

# zap-extensions beta
git clone --branch beta https://github.com/zapbot/zap-extensions.git zap-extensions_beta
cd zap-extensions_beta
git remote add upstream https://github.com/zaproxy/zap-extensions.git
cd ..

# zap-extensions alpha
git clone --branch alpha https://github.com/zapbot/zap-extensions.git zap-extensions_alpha
cd zap-extensions_alpha
git remote add upstream https://github.com/zaproxy/zap-extensions.git
cd ..

# zap-core-help
git clone https://github.com/zapbot/zap-core-help.git
cd zap-core-help
git remote add upstream https://github.com/zaproxy/zap-core-help.git
cd ..

# zaproxy coverity_scan
git clone --branch coverity_scan https://github.com/zapbot/zaproxy.git zaproxy_coverity
cd zaproxy_coverity
git remote add upstream https://github.com/zaproxy/zaproxy.git
cd ..



