#!/usr/bin/env python
# This script generates the dynamic data for http://zapbot.github.io/zap-mgmt-scripts/downloads.html

import glob,json,os,sys

# The file names
REL = '2.6.0'
CORE = 'ZAP_2.6.0_Core.tar.gz'
CROSS = 'ZAP_2.6.0_Crossplatform.zip'
LINUX = 'ZAP_2.6.0_Linux.tar.gz'
UNIX = 'ZAP_2_6_0_unix.sh'
MAC = 'ZAP_2_6_0_macos.dmg'
WIN32 = 'ZAP_2_6_0_windows-x32.exe'
WIN64 = 'ZAP_2_6_0_windows.exe'

counts = {}
files = sorted(glob.glob('../zap-mgmt-scripts_gh-pages/stats/releases-*'))
# Option to just show the last 180 days to prevent the chart getting too big
files = files[-180:]
first = 1
for file in files:
  with open(file) as stats_file:
    stats = json.load(stats_file)

  for stat in stats:
    if (stat['name'] == REL):
      assets = {}
      for asset in stat['assets']:
        name = asset['name']
        count = asset['download_count']
        if (name in counts):
          # Ignore negative numbers - can happen when files are replaced
          assets[name] = max((count - counts[name]), 0)
        else:
          assets[name] = count
        counts[name] = count
      if (first):
        # Ignore the first as its just for getting a baseline
        first = 0
      else:
        print "        ['%s', %d, %d, %d, %d, %d, %d, %d, '']," % (file[-15:-5], 
          assets[WIN64], assets[WIN32], assets[UNIX], assets[LINUX], assets[MAC], assets[CROSS], assets[CORE])
    
