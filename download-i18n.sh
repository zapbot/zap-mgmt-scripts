# Trigger the Crowdin builds
# Requires a ../zap-admin/build/crowdin-api-keys file present with valid credentials

# Assume we're running in the zap-mgmt-scripts directory
cd ..

cd zap-admin/build
ant -f build.xml crowdin-trigger-export-packages
ant -f build.xml crowdin-download-translations

