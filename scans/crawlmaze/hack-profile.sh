# A nasty little script to create the zap-client-profile
# as Selenium doesnt seem to allow us to do this in the ZAP Docker containers

mkdir -p /home/zap/.mozilla/firefox/abc5jhgf.zap-client-profile/
echo "[Profile0]" >> /home/zap/.mozilla/firefox/profiles.ini
echo "Name=zap-client-profile" >> /home/zap/.mozilla/firefox/profiles.ini
echo "IsRelative=1" >> /home/zap/.mozilla/firefox/profiles.ini
echo "Path=abc5jhgf.zap-client-profile" >> /home/zap/.mozilla/firefox/profiles.ini
