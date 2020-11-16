#!/bin/bash
# Runs ZAP against Owasp VulnerableApp with the specified options, generates the report and issues a PR to update it
# Parameters:
#	-a					Run the Ajax spider (in addition to the traditional one)
#	-e expected-score	Expected score string
#	-n name				Base name to use for the result files
#	-t text				Text to use in the summary table for the add-ons installed
#	-z zap-options		Options to be passed directly to the ZAP command line call 
#
# Some example calls:
# ./zap-vs-vulnerableApp.sh -d "owasp/zap2docker-weekly" -e "66" -n "vulnerableApp-weekly-RB-M-M" -t "Rel,Beta"
# ./zap-vs-vulnerableApp.sh -d "owasp/zap2docker-weekly" -e "66" -p "St-High-Th-Med" -n "vulnerableApp-weekly-RB-H-M" -t "Rel,Beta"
# ./zap-vs-vulnerableApp.sh -d "owasp/zap2docker-weekly" -e "66" -n "vulnerableApp-weekly-RBA-M-M" -t "Rel,Beta,Alpha" -z "-addoninstall ascanrulesAlpha"

USAGE="Usage: $0 [-a] -d docker-image [-e expected-score] -n name [-t text] [-z zap-options]"

# Handle the options
expected=''
name=''
policy='Default Policy'
text=''
score_opt=''

while getopts "ae:n:p:t:" optname
  do
    case "$optname" in
      "a")
        # Ajax Spider
        score_opt="-a"
        ;;
      "e")
        # The expected score string
        expected=$OPTARG
        ;;
      "n")
        # The name to use in the results files
        name=$OPTARG
        ;;
      "p")
        # Scan Policy (mandatory)
        policy=$OPTARG
        ;;
      "t")
        text=$OPTARG
        ;;
      "?")
        echo "Unknown option $OPTARG"
        ;;
      ":")
        echo "No argument value for option $OPTARG"
        ;;
      *)
      # Should not occur
        echo "Unknown error while processing options"
        ;;
    esac
  done
# Check for the mandatory ones
if [ "$name" == "" ]
then
  echo "Missing name"
  echo $USAGE
  exit 2
fi
if [ "$policy" == "" ]
then
  echo "Missing policy"
  echo $USAGE
  exit 2
fi

# Git stuff
git config --global user.name "zapbot"
git config --global user.email "zapbot@zaproxy.org"

mkdir wrk
# Start a new out.txt file with the date
date > wrk/out.txt

echo Let ZAP start up...
sleep 60

# Spider and scan the app
python3 vulnerableApp_spider_scan.py $score_opt -p "$policy" -z localhost -w 127.0.0.1 >> wrk/out.txt
cat wrk/out.txt

# Generate the report
python3 vulnerableApp_score.py -h localhost > wrk/summary.txt
cat wrk/summary.txt

echo "====" >> wrk/out.txt
echo "Summary" >> wrk/out.txt
cat wrk/summary.txt >> wrk/out.txt

echo "<TR>" > ${name}.summary
echo "<td>" `cat wrk/summary.txt | grep ZAP | awk -F ' ' '{print $2}'` "</td>" >> ${name}.summary

echo "<td>Owasp VulnerableApp</td>" >> ${name}.summary
echo "<td>$text</td>" >> ${name}.summary
echo "<td>$policy</td>" >> ${name}.summary

echo "<td>" `date --rfc-3339 date` "</td>" >> ${name}.summary

# The score and expected columns
SC=$(cat wrk/summary.txt | grep Score | awk -F ' ' '{print $2}')
echo "<td><a href=\"reports/${name}.html\">${SC} &#37;</a></td>" >> ${name}.summary
if [ "$SC" -eq "$expected" ]; then
  echo "<td>${expected} &#37;</td>" >> ${name}.summary
elif [ "$SC" -gt "$expected" ]; then
  echo "<td><span style=\"color:green\">${expected} &#37;</span></td>" >> ${name}.summary
else
  echo "<td><span style=\"color:red\">${expected} &#37;</span></td>" >> ${name}.summary
fi

echo "<td>" `cat wrk/summary.txt | grep urls | awk -F ' ' '{print $2}'` "</td>" >> ${name}.summary
echo "<td>" `cat wrk/summary.txt | grep Took | awk -F ' ' '{print $2}'` "</td>" >> ${name}.summary

# TODO get hold of the ZAP logs
#ERRS=$(grep -c ERROR ~/zap-mgmt-scripts/reports/${name}.logs.txt) >> ${name}.summary
#echo "<td><a href=\"reports/${name}.logs.txt\">${ERRS}</a></td>" >> ${name}.summary
echo "</tr>" >> ${name}.summary

cat ${name}.summary

git clone -b gh-pages https://github.com/zapbot/zap-mgmt-scripts.git

# Save and push to github
mv ${name}.summary zap-mgmt-scripts/reports/
mv report.html zap-mgmt-scripts/reports/${name}.html

cd zap-mgmt-scripts

git add reports

cat scan.head reports/*.summary scan.tail > scans.html
git add scans.html

git commit -m "Report ${name}"
git remote set-url origin https://zapbot:$ZAPBOT_TOKEN@github.com/zapbot/zap-mgmt-scripts.git
git push origin

