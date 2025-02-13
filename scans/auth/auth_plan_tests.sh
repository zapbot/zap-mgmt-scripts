#!/bin/bash
# Script for testing Automation Framework features

RES=0

mkdir -p /zap/wrk/output
OUTPUT=/zap/wrk/output/output.yml
# Remove output file in case it already exists
rm -f $OUTPUT

echo "Authentication tests"
echo

cd /zap/wrk/scans/auth/plans_and_scripts/

summary="\nSummary:\n"
INDENT="  "

for TARGET in *
do
    if [ -d "$TARGET" ]
    then
        echo
        cd "$TARGET"
        echo "$TARGET:"|tee -a "$OUTPUT" > /dev/null
        for file in *.yaml
        do
            echo "Target: $TARGET Plan: $file"
            TYPE=$(echo "$file"|cut -d"." -f1)":"
            echo -ne "$INDENT$TYPE"|tee -a "$OUTPUT" > /dev/null

            /zap/zap.sh -cmd -autorun /zap/wrk/scans/auth/plans_and_scripts/"$TARGET"/"$file"
            RET=$?

            if [ "$RET" != 0 ] 
            then
                echo "ERROR"
                echo " false"|tee -a "$OUTPUT" > /dev/null
                summary="${summary}  Plan: $file\tERROR\n"
                RES=1
            else
                echo "PASS"
                echo " true"|tee -a "$OUTPUT" > /dev/null
                summary="${summary}  Plan: $file\tPASS\n"
            fi
            sleep 2
        done
        if [ -f notes.txt ]
        then
            echo -ne "$INDENT"|tee -a "$OUTPUT" > /dev/null
            echo -ne "note: "|tee -a "$OUTPUT" > /dev/null
            echo \""$(cat notes.txt)"\"|tee -a "$OUTPUT" > /dev/null
        fi
        cd ..
    fi
done

echo -e "$summary"
echo "Exit Code: $RES"

cat "$OUTPUT"

exit $RES
