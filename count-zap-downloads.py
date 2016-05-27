#!/usr/bin/env python
# This script generates the dynamic data for http://zapbot.github.io/zap-mgmt-scripts/downloads.html

import glob,json,os,sys

# The file names
REL = '2.4.3'
CORE = 'ZAP_2.4.3_Core.tar.gz'
CROSS = 'ZAP_2.4.3_Cross_Platform.zip'
LINUX = 'ZAP_2.4.3_Linux.tar.gz'
MAC = 'ZAP_2.4.3_Mac_OS_X.dmg'
WIN = 'ZAP_2.4.3_Windows.exe'

counts = {}
files = sorted(glob.glob('../zap-mgmt-scripts_gh-pages/stats/releases-*'))
# Option to just show the last 90 days to prevent the chart getting too big, currently disabled
#files = files[-91:]
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
          assets[name] = (count - counts[name])
        else:
          assets[name] = count
        counts[name] = count
      if (first):
        # Ignore the first as its just for getting a baseline
        first = 0
      else:
        print "        ['%s', %d, %d, %d, %d, %d, '']," % (file[-15:-5], assets[WIN], assets[LINUX], assets[MAC], assets[CROSS], assets[CORE])
    
