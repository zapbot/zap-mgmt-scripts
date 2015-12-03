#!/bin/bash
# Runs ZAP weekly against wavsep with default options, generates the report and issues a PR to update it

EXPECTED="Score 66"
REP="wavsep-1.5-weekly-RB-H-M"

git config --global user.name "zapbot"
git config --global user.email "zapbot@zaproxy.org"

mkdir ~/wrk
rm ~/wrk/out.txt

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

docker pull owasp/zap2docker-weekly
ZPCID=$(sudo docker run -u zap -p 8090:8090 -d owasp/zap2docker-weekly zap.sh -daemon -port 8090 -host 0.0.0.0 -config api.disablekey=true -addoninstall ascanrulesAlpha)

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
python ~/zap-mgmt-scripts/wavsep/wavsep-1.5-spider-scan-H-M.py -z $ZPIP -w $WSIP >> ~/wrk/out.txt

# Save the logs
LOG="~/zap-mgmt-scripts_gh-pages/reports/${REP}.logs.txt"
docker logs $ZPCID > ~/zap-mgmt-scripts_gh-pages/reports/${REP}.logs.txt


# Generate the report
python ~/zap-mgmt-scripts/wavsep/wavsep-score.py -h $ZPIP > ~/wrk/summary.txt
echo "====" >> ~/wrk/out.txt
echo "Summary" >> ~/wrk/out.txt
cat ~/wrk/summary.txt >> ~/wrk/out.txt

echo "<TR>" > ${REP}.summary
echo "<td>" `cat ~/wrk/summary.txt | grep ZAP | awk -F ' ' '{print $2}'` "</td>" >> ${REP}.summary

# Change these manually
echo "<td>wavsep 1.5</td>" >> ${REP}.summary
echo "<td>Rel, Beta</td>" >> ${REP}.summary
echo "<td>H</td>" >> ${REP}.summary
echo "<td>M</td>" >> ${REP}.summary

echo "<td>" `date --rfc-3339 date` "</td>" >> ${REP}.summary
SC=$(cat ~/wrk/summary.txt | grep Score | awk -F ' ' '{print $2}')
echo "<td><a href=\"reports/${REP}.html\">${SC}</a></td>" >> ${REP}.summary
echo "<td>" `cat ~/wrk/summary.txt | grep urls | awk -F ' ' '{print $2}'` "</td>" >> ${REP}.summary
echo "<td>" `cat ~/wrk/summary.txt | grep Took | awk -F ' ' '{print $2}'` "</td>" >> ${REP}.summary

ERRS=$(grep -c ERROR ~/zap-mgmt-scripts_gh-pages/reports/${REP}.logs.txt) >> ${REP}.summary
echo "<td><a href=\"reports/${REP}.logs.txt\">${ERRS}</a></td>" >> ${REP}.summary
echo "</tr>" >> ${REP}.summary

cat ${REP}.summary

# If present ~/.awssns should contain the AWS SNS topic to post to
AWSSNSF=$(echo ~/.awssns)

if [ "$SC" == "" ]; then
  # Something went wrong score, send an alert
  AWSSNS=$(cat ~/.awssns)
  OUTFILE=$(cat ~/wrk/out.txt)
  aws sns publish --subject "ZAP ${REP} Failed to run properly" --message "$OUTFILE" --topic $AWSSNS
  exit
elif [ "$SC" != "$EXPECTED" ]; then
  # Unexpected score, send an alert
  AWSSNS=$(cat ~/.awssns)
  aws sns publish --subject "ZAP ${REP} Unexpected score" --message "Expected $EXPECTED got $SC" --topic $AWSSNS
fi

# Save and push to github
mv ${REP}.summary ~/zap-mgmt-scripts_gh-pages/reports/
mv report.html ~/zap-mgmt-scripts_gh-pages/reports/${REP}.html

cd ~/zap-mgmt-scripts_gh-pages
git add reports

cat scan.head reports/*.summary scan.tail > scans.html
git add scans.html

git commit -m "Report ${REP}"
git push origin

