# Record the download stats

git config --global push.default simple

DATE=$(date --rfc-3339 date)
curl https://api.github.com/repos/zaproxy/zaproxy/releases > ../zap-mgmt-scripts_gh-pages/stats/releases-${DATE}.json
curl https://api.github.com/repos/zaproxy/zap-extensions/releases >  ../zap-mgmt-scripts_gh-pages/stats/ext-releases-${DATE}.json

# Generate the ZAP download page

cat ../zap-mgmt-scripts_gh-pages/download.head > ../zap-mgmt-scripts_gh-pages/downloads.html
python count-zap-downloads.py >> ../zap-mgmt-scripts_gh-pages/downloads.html
cat ../zap-mgmt-scripts_gh-pages/download.tail >> ../zap-mgmt-scripts_gh-pages/downloads.html

# Generate the ZAP add-ons page

cat ../zap-mgmt-scripts_gh-pages/addon.head > ../zap-mgmt-scripts_gh-pages/addons.html
python count-addon-downloads.py >> ../zap-mgmt-scripts_gh-pages/addons.html
cat ../zap-mgmt-scripts_gh-pages/addon.tail >> ../zap-mgmt-scripts_gh-pages/addons.html

cd  ../zap-mgmt-scripts_gh-pages/

# Push to the repo

git pull
git add addons.html downloads.html stats
git commit -m "Stats for ${DATE}"
git push origin
