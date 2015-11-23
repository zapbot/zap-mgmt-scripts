# Runs all of the scripts required before scanning an app

# Assume we're running in the zap-mgmt-scripts directory
cd ../zaproxy
/usr/bin/git pull
cd ..
cd zap-mgmt-scripts
./stop-delete-docker.sh
