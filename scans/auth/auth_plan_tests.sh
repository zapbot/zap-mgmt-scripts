#!/bin/bash
# Script for testing Automation Framework features

runplan()
{
    TARGET=$1
    FILE=$2
    TYPE=$3
    echo "Target: $TARGET Plan: $FILE"
    echo -ne "$INDENT"- type: "$TYPE\n"|tee -a "$OUTPUT" > /dev/null
    echo -ne "$INDENT$INDENT"auth:|tee -a "$OUTPUT" > /dev/null

    /zap/zap.sh -cmd -autorun "$FILE"
    RET=$?
    if [[ $TYPE == "stdbba" ]]
    then
        AUTHREPORT=../../auth-report.json
    else
        AUTHREPORT=auth-report.json
    fi
    if [ -f $AUTHREPORT ]
    then
        echo "Using data from the authentication report"
        AUTH=`jq -r '.summaryItems[] | select(.key == "auth.summary.auth") | .passed' $AUTHREPORT`
        
        if [ "$AUTH" == "true" ]
        then
            echo "PASS"
            echo " true"|tee -a "$OUTPUT" > /dev/null
            summary="${summary}  Plan: $TYPE\tPASS\n"
            getreportdetails $AUTHREPORT
        else
            if [ "$AUTH" != "false" ]
            then
                echo "WARNING: did not get an expected value for the given key"
            fi
            echo "ERROR"
            echo " false"|tee -a "$OUTPUT" > /dev/null
            summary="${summary}  Plan: $TYPE\tERROR\n"
            getreportdetails $AUTHREPORT
            RES=1
        fi 
        rm $AUTHREPORT
    else
        echo "Using the result of the plan"
        if [ "$RET" != 0 ] 
        then
            echo "ERROR"
            echo " false"|tee -a "$OUTPUT" > /dev/null
            summary="${summary}  Plan: $TYPE\tERROR\n"
            RES=1
        else
            echo "PASS"
            echo " true"|tee -a "$OUTPUT" > /dev/null
            summary="${summary}  Plan: $TYPE\tPASS\n"
        fi
    fi
}

getreportdetails()
{
    AUTHREPORT=$1
    USER_SUCCESS=`jq -r '.summaryItems[] | select(.key == "auth.summary.username") | .passed' $AUTHREPORT`
    echo "$INDENT$INDENT"username: $USER_SUCCESS|tee -a "$OUTPUT" > /dev/null
    PASS_SUCCESS=`jq -r '.summaryItems[] | select(.key == "auth.summary.password") | .passed' $AUTHREPORT`
    echo "$INDENT$INDENT"password: $PASS_SUCCESS|tee -a "$OUTPUT" > /dev/null
    SESS_SUCCESS=`jq -r '.summaryItems[] | select(.key == "auth.summary.session") | .passed' $AUTHREPORT`
    echo "$INDENT$INDENT"session: $SESS_SUCCESS|tee -a "$OUTPUT" > /dev/null
    VERIF_SUCCESS=`jq -r '.summaryItems[] | select(.key == "auth.summary.verif") | .passed' $AUTHREPORT`
    echo "$INDENT$INDENT"verification: $VERIF_SUCCESS|tee -a "$OUTPUT" > /dev/null
}

RES=0

mkdir -p /zap/wrk/output
OUTPUT=/zap/wrk/output/output.yml
# Remove output file in case it already exists
rm -f $OUTPUT

echo "Authentication tests"
echo

cd /zap/wrk/scans/auth/plans_and_scripts/

summary="\n\nSummary:\n========\n"
INDENT="  "

for TARGET in *
do
    if [ -d "$TARGET" ]
    then
        summary="${summary}$TARGET\n"
        echo
        cd "$TARGET"
        echo "$TARGET:"|tee -a "$OUTPUT" > /dev/null
        if [ -f "config" ]
        then
            set -o allexport
            source "config"
            set +o allexport

            export password=$(eval echo \$\{TARGET\}_pass)
            export zappassword=${!password}

            export username=$(eval echo \$\{TARGET\}_user)
            export zapusername=${!username}
            
            runplan $TARGET /zap/wrk/scans/auth/bba-auth-test.yaml "stdbba"
        else
            echo "No $TARGET/config file"
        fi
        
        shopt -s nullglob  # May be no yaml files
        for file in *.yaml
        do
            runplan $TARGET /zap/wrk/scans/auth/plans_and_scripts/$TARGET/$file $(echo "$file"|cut -d"." -f1)
            sleep 2
        done
        shopt -u nullglob

        if [ -f notes.txt ]
        then
            echo -ne "$INDENT"|tee -a "$OUTPUT" > /dev/null
            echo -ne "- note: "|tee -a "$OUTPUT" > /dev/null
            echo "\"$(cat notes.txt)\""|tee -a "$OUTPUT" > /dev/null
        fi
        cd ..
    fi
done

echo -e "$summary"

cat "$OUTPUT"
