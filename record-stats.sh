# Record the download stats

git config --global push.default simple

DATE=$(date --rfc-3339 date)
curl https://api.github.com/repos/zaproxy/zaproxy/releases > ~/zap-mgmt-scripts_gh-pages/stats/releases-${DATE}.json
curl https://api.github.com/repos/zaproxy/zap-extensions/releases >  ~/zap-mgmt-scripts_gh-pages/stats/ext-releases-${DATE}.json
cd  ~/zap-mgmt-scripts_gh-pages/

git pull
git add stats
git commit -m "Stats for ${DATE}"
git push origin
