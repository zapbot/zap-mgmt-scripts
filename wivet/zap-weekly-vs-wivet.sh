# Runs ZAP weekly against wivet with default options, generates the report and issues a PR to update it

EXPECTED="Score 51"
REP="wivet-weekly"

git config --global user.name "zapbot"
git config --global user.email "zapbot@zaproxy.org"

# Download and start new docker instances

docker pull andresriancho/wivet
WSCID=$(docker run -d -p 443:443 andresriancho/wivet)

IP=$(docker inspect $WSCID | grep IPAddress | tail -1)
IP=$(echo $IP | awk '{print substr($0,15)}')

WSIP=$(echo ${IP::-2})
echo Wivet IP = $WSIP

docker pull owasp/zap2docker-weekly
ZPCID=$(docker run -u zap -p 8090:8090 -d owasp/zap2docker-weekly zap-x.sh -daemon -port 8090 -host 0.0.0.0 -config api.disablekey=true -config ajaxSpider.clickDefaultElems=False)

IP=$(docker inspect $ZPCID | grep IPAddress | tail -1)
IP=$(echo $IP | awk '{print substr($0,15)}')

ZPIP=$(echo ${IP::-2})
echo ZAP IP = $ZPIP

echo Let ZAP start up...
sleep 20

# Spider and scan the app
python ~/zap-mgmt-scripts/wivet/wivet-spider-ajax.py -z $ZPIP -w $WSIP > result

# Save the logs
LOG="~/zap-mgmt-scripts_gh-pages/reports/${REP}.logs.txt"
docker logs $ZPCID > ~/zap-mgmt-scripts_gh-pages/reports/${REP}.logs.txt

echo "<tr>" > ${REP}.summary
echo "<td>" `cat result | grep ZAP | awk -F ' ' '{print $2}'` "</td>" >> ${REP}.summary

# Change these manually
echo "<td>wivet</td>" >> ${REP}.summary
echo "<td>Ajax</td>" >> ${REP}.summary
echo "<td>-</td>" >> ${REP}.summary
echo "<td>-</td>" >> ${REP}.summary

echo "<td>" `date --rfc-3339 date` "</td>" >> ${REP}.summary
echo "<td>" `cat result | grep Score | awk -F ' ' '{print $2}'` "</td>" >> ${REP}.summary
echo "<td>" `cat result | grep Pages | awk -F ' ' '{print $2}'` "</td>" >> ${REP}.summary
echo "<td>" `cat result | grep Time | awk -F ' ' '{print $2}'` "</td>" >> ${REP}.summary

ERRS=$(grep -c ERROR ~/zap-mgmt-scripts_gh-pages/reports/${REP}.logs.txt) >> ${REP}.summary
echo "<td><a href=\"reports/${REP}.logs.txt\">${ERRS}</a></td>" >> ${REP}.summary
echo "</tr>" >> ${REP}.summary

cat ${REP}.summary

# If present ~/.awssns should contain the AWS SNS topic to post to
AWSSNSF=$(echo ~/.awssns)

# TODO SC is never set up ;)
if [ "$SC" != "$EXPECTED" ]; then
  # Unexpected score, send an alert
  AWSSNS=$(cat ~/.awssns)
  aws sns publish --subject "ZAP ${REP} Unexpected score" --message "Expected $EXPECTED got $SC" --topic $AWSSNS
fi

# Save and push to github
mv ${REP}.summary ~/zap-mgmt-scripts_gh-pages/reports/

cd ~/zap-mgmt-scripts_gh-pages
git add reports

cat scan.head reports/*.summary scan.tail > scans.html
git add scans.html

git commit -m "Latest report weekly vs wivet"
git push origin

