# Runs ZAP weekly against wavsep with default options, generates the report and issues a PR to update it

EXPECTED="Score 51"

git config --global user.name "zapbot"
git config --global user.email "zapbot@zaproxy.org"

# Download and start new docker instances

docker pull vianma/wavsep:v15
WSCID=$(sudo docker run -d -p 8080:8080 vianma/wavsep:v15)

IP=$(docker inspect $WSCID | grep IPAddress | tail -1)
IP=$(echo $IP | awk '{print substr($0,15)}')

WSIP=$(echo ${IP::-2})
echo Wavsep IP = $WSIP

docker pull owasp/zap2docker-weekly
ZPCID=$(sudo docker run -u zap -p 8090:8090 -d owasp/zap2docker-weekly zap.sh -daemon -port 8090 -host 0.0.0.0 -config api.disablekey=true -addoninstall ascanrulesAlpha)

IP=$(docker inspect $ZPCID | grep IPAddress | tail -1)
IP=$(echo $IP | awk '{print substr($0,15)}')

ZPIP=$(echo ${IP::-2})
echo ZAP IP = $ZPIP

echo Let ZAP start up...
sleep 20

# Spider and scan the app
python ~/zap-mgmt-scripts/wavsep/wavsep-1.5-spider-scan.py -z $ZPIP -w $WSIP

# Generate the report
SC=$(python ~/zap-mgmt-scripts/wavsep/wavsep-score.py -h $ZPIP| grep Score)

# If present ~/.awssns should contain the AWS SNS topic to post to
AWSSNSF=$(echo ~/.awssns)

if [ "$SC" != "$EXPECTED" ]; then
  # Unexpected score, send an alert
  AWSSNS=$(cat ~/.awssns)
  aws sns publish --subject "ZAP Release Vs Wavsep 1.5 Unexpected score" --message "Expected $EXPECTED got $SC" --topic $AWSSNS
fi

# Save and push to github
mv report.html ~/zap-mgmt-scripts_gh-pages/reports/wavsep-1.5-weekly-RB-M-M.html
docker logs $ZPCID > ~/zap-mgmt-scripts_gh-pages/reports/wavsep-1.5-weekly-RB-M-M.logs.txt

cd ~/zap-mgmt-scripts_gh-pages
git add reports

git commit -m "Latest report weekly vs wavsep"
git push origin

