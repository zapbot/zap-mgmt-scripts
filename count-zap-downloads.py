#!/usr/bin/env python
# This script generates the dynamic data for http://zapbot.github.io/zap-mgmt-scripts/downloads.html

import glob,json,os,sys

# The file names
REL = 'v2.9.0'
CORE = 'ZAP_2.9.0_Core.zip'
CROSS = 'ZAP_2.9.0_Crossplatform.zip'
LINUX = 'ZAP_2.9.0_Linux.tar.gz'
UNIX = 'ZAP_2_9_0_unix.sh'
MAC = 'ZAP_2.9.0.dmg'
WIN32 = 'ZAP_2_9_0_windows-x32.exe'
WIN64 = 'ZAP_2_9_0_windows.exe'

counts = {}
files = sorted(glob.glob('./stats/releases-*'))
# Option to just show the last 180 days to prevent the chart getting too big
files = files[-180:]
for file in files:
  with open(file) as stats_file:
    stats = json.load(stats_file)

  if (stats['name'] == REL):
    assets = {}
    for asset in stats['assets']:
      name = asset['name']
      count = asset['download_count']
      if (name in counts):
        # Ignore negative numbers - can happen when files are replaced
        assets[name] = max((count - counts[name]), 0)
      else:
        assets[name] = count
      counts[name] = count
    if (files.index(file) == 0):
      # Ignore the first as its just for getting a baseline
      continue
    else:
      print("        ['%s', %d, %d, %d, %d, %d, %d, %d, '']," % (file[-15:-5], 
        assets[WIN64], assets[WIN32], assets[UNIX], assets[LINUX], assets[MAC], assets[CROSS], assets[CORE]))