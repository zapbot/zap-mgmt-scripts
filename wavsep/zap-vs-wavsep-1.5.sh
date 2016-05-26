#!/bin/bash
# Runs ZAP against wavsep with the specified options, generates the report and issues a PR to update it
# Parameters:
#	-a					Run the Ajax spider (in addition to the traditional one)
#	-d docker-image		Name of the ZAP docker image to use, typically owasp/zap2docker-weekly or owasp/zap2docker-stable
#	-e expected-score	Expected score string
#	-n name				Base name to use for the result files
#	-t text				Text to use in the summary table for the add-ons installed
#	-z zap-options		Options to be passed directly to the ZAP command line call 
#
# Some example calls:
# ./zap-vs-wavsep-1.5.sh -d "owasp/zap2docker-weekly" -e "66" -n "wavsep-1.5-weekly-RB-M-M" -t "Rel,Beta"
# ./zap-vs-wavsep-1.5.sh -d "owasp/zap2docker-weekly" -e "66" -p "St-High-Th-Med" -n "wavsep-1.5-weekly-RB-H-M" -t "Rel,Beta"
# ./zap-vs-wavsep-1.5.sh -d "owasp/zap2docker-weekly" -e "66" -n "wavsep-1.5-weekly-RBA-M-M" -t "Rel,Beta,Alpha" -z "-addoninstall ascanrulesAlpha"

USAGE="Usage: $0 [-a] -d docker-image [-e expected-score] -n name [-t text] [-z zap-options]"

# Handle the options
docker=''
expected=''
name=''
policy='Default Policy'
text=''
zap_opt=''
score_opt=''

while getopts "ad:e:n:p:t:z:" optname
  do
    case "$optname" in
      "a")
        # Ajax Spider
        score_opt="-a"
        ;;
      "d")
        # Docker image (mandatory)
        docker=$OPTARG
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
      "z")
        # ZAP command line options
        zap_opt=$OPTARG
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
if [ "$docker" == "" ]
then
  echo "Missing docker"
  echo $USAGE
  exit 2
fi
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

# The wrk directory will probably exist, but just in case..
mkdir ~/wrk
# Start a new out.txt file with the date
date > ~/wrk/out.txt

# Download and start new docker instances
docker pull vianma/wavsep:v15
WSCID=$(sudo docker run -d -p 8080:8080 vianma/wavsep:v15)
echo "WSCID=$WSCID" >> ~/wrk/out.txt

IP=$(docker inspect $WSCID | grep IPAddress | tail -1)
echo "IP=$IP" >> ~/wrk/out.txt
IP=$(echo $IP | awk '{print substr($0,15)}')
echo "IP=$IP" >> ~/wrk/out.txt

WSIP=$(echo ${IP::-2})
echo "WSIP=$WSIP" >> ~/wrk/out.txt
echo Wavsep IP = $WSIP

docker pull $docker
ZPCID=$(sudo docker run -u zap -p 8090:8090 -d $docker zap-x.sh -daemon -port 8090 -host 0.0.0.0 -config api.disablekey=true $zap_opt)

IP=$(docker inspect $ZPCID | grep IPAddress | tail -1)
IP=$(echo $IP | awk '{print substr($0,15)}')

ZPIP=$(echo ${IP::-2})
echo "====" >> ~/wrk/out.txt
echo "ZPCID=$ZPCID" >> ~/wrk/out.txt
echo "ZPIP=$ZPIP" >> ~/wrk/out.txt
echo ZAP IP = $ZPIP

echo Let ZAP start up...
sleep 20

# Spider and scan the app
python ~/zap-mgmt-scripts/wavsep/wavsep-1.5-spider-scan.py $score_opt -p "$policy" -z $ZPIP -w $WSIP >> ~/wrk/out.txt

# Save the logs
LOG="~/zap-mgmt-scripts_gh-pages/reports/${name}.logs.txt"
docker logs $ZPCID > ~/zap-mgmt-scripts_gh-pages/reports/${name}.logs.txt


# Generate the report
python ~/zap-mgmt-scripts/wavsep/wavsep-score.py -h $ZPIP > ~/wrk/summary.txt
echo "====" >> ~/wrk/out.txt
echo "Summary" >> ~/wrk/out.txt
cat ~/wrk/summary.txt >> ~/wrk/out.txt

echo "<TR>" > ${name}.summary
echo "<td>" `cat ~/wrk/summary.txt | grep ZAP | awk -F ' ' '{print $2}'` "</td>" >> ${name}.summary

echo "<td>wavsep 1.5</td>" >> ${name}.summary
echo "<td>$text</td>" >> ${name}.summary
echo "<td>$policy</td>" >> ${name}.summary

echo "<td>" `date --rfc-3339 date` "</td>" >> ${name}.summary

# The score and expected columns
SC=$(cat ~/wrk/summary.txt | grep Score | awk -F ' ' '{print $2}')
echo "<td><a href=\"reports/${name}.html\">${SC} &#37;</a></td>" >> ${name}.summary
if [ "$SC" -eq "$expected" ]; then
  echo "<td>${expected} &#37;</td>" >> ${name}.summary
elif [ "$SC" -gt "$expected" ]; then
  echo "<td><span style=\"color:green\">${expected} &#37;</span></td>" >> ${name}.summary
else
  echo "<td><span style=\"color:red\">${expected} &#37;</span></td>" >> ${name}.summary
fi

echo "<td>" `cat ~/wrk/summary.txt | grep urls | awk -F ' ' '{print $2}'` "</td>" >> ${name}.summary
echo "<td>" `cat ~/wrk/summary.txt | grep Took | awk -F ' ' '{print $2}'` "</td>" >> ${name}.summary

ERRS=$(grep -c ERROR ~/zap-mgmt-scripts_gh-pages/reports/${name}.logs.txt) >> ${name}.summary
echo "<td><a href=\"reports/${name}.logs.txt\">${ERRS}</a></td>" >> ${name}.summary
echo "</tr>" >> ${name}.summary

cat ${name}.summary

# If present ~/.awssns should contain the AWS SNS topic to post to
AWSSNSF=$(echo ~/.awssns)
OUTFILE=$(cat ~/wrk/out.txt)

if [ "$SC" == "" ]; then
  # Something went wrong score, send an alert
  AWSSNS=$(cat ~/.awssns)
  aws sns publish --subject "ZAP ${name} Failed to run properly" --message "$OUTFILE" --topic $AWSSNS
  exit
elif [ "$SC" != "$expected" ]; then
  # Unexpected score, send an alert
  AWSSNS=$(cat ~/.awssns)
  aws sns publish --subject "ZAP ${name} Expected '$expected' got '$SC'" --message "$OUTFILE" --topic $AWSSNS
fi

# Save and push to github
mv ${name}.summary ~/zap-mgmt-scripts_gh-pages/reports/
mv report.html ~/zap-mgmt-scripts_gh-pages/reports/${name}.html

cd ~/zap-mgmt-scripts_gh-pages
git pull
git add reports

cat scan.head reports/*.summary scan.tail > scans.html
git add scans.html

git commit -m "Report ${name}"
git push origin

