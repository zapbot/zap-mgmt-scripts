# This script allows you to run the auth test you specify in your ZAP dev environment.
# You need to either be in the top level zap-mgmt-scripts directory or in the scans/auth directory.
# The scans/auth/all_vars.env must be present and contain suitable credentials for the target.
# It will default to the "standard" BBA auth test unless you also specify the plan to use, with or without the .yaml extension.
# To make it easier to see whats going change the AF plan to use a non headless browser and to display the report.

MGMT_DIR=`pwd`
BASE_DIR="$MGMT_DIR/scans/auth"

echo "Num params $#"

if [ "$#" -eq 0 ]; then
    echo "Usage: $0 <dir> [<plan>]"
    exit 1
fi

if [ ! -d "$BASE_DIR" ]
then
	if [ -d "plans_and_scripts" ]
	then
		MGMT_DIR=`realpath ../..`
		BASE_DIR="$MGMT_DIR/scans/auth"
	else
		echo "Not running in top zap_mgmt_scripts dir or in the scans/auth dir."
		echo "Run in one of those dirs or update this script to handle your use case :)"
	    exit 1
	fi
fi

ZAP_DIR="$MGMT_DIR/../zaproxy"
if [ ! -d "$BASE_DIR" ]
then
    echo "No ZAP directory: $ZAP_DIR"
    exit 1
fi

PLAN_DIR="$BASE_DIR/plans_and_scripts"
TEST=$1
TEST_DIR="$PLAN_DIR/$TEST"
if [ "$#" -eq 2 ]
then
	# Support plan name with and without .yaml
    if [[ "$2" == *.yaml ]]
    then
	    PLAN=$2
	else
	    PLAN=$2.yaml
	fi
fi

if [ ! -d "$TEST_DIR" ]
then
    echo "No such directory: $TEST_DIR"
    echo "Valid directories:"
    cd $PLAN_DIR
    ls -d */
    exit 1
fi

if [ ! "$PLAN" == "" ] && [ ! -f "$TEST_DIR/$PLAN" ]
then
    echo "No such plan: $TEST_DIR/$PLAN"
    echo "Valid plans:"
    cd $TEST_DIR
    ls *.yaml
    exit 1
fi

VARS_FILE="$BASE_DIR/all_vars.env"

if [ ! -f "$VARS_FILE" ]
then
    echo "No file $VARS_FILE"
    echo "This file much be present and contain suitable usernames and passwords."
    exit 1
fi

# Set up all of the env vars
set -o allexport
source "$VARS_FILE"
source "$TEST_DIR/config"
set +o allexport
export password=$(eval echo \$\{TEST\}_pass)
export zappassword=${!password}
export username=$(eval echo \$\{TEST\}_user)
export zapusername=${!username}

echo "Testing $zapsite with user $zapusername"
# Uncomment if you need to double check the password is correct - some special characters need escaping
# echo "Password $zappassword"

cd $ZAP_DIR

if [ "$PLAN" == "" ]
then
	./gradlew run --args="-autorun $BASE_DIR/bba-auth-test.yaml"
else
	./gradlew run --args="-autorun $TEST_DIR/$PLAN"
fi

