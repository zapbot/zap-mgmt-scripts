#!/usr/bin/env python
# This script generates the dynamic data for http://zapbot.github.io/zap-mgmt-scripts/addons.html

import glob,json,os,sys

TAG = '2.4'

# Number of days to chart
days = 7

# Maintain running totals so we can work out the differences
counts = {}
# The maximum number of download of each add-on over all days
max = {}
# The number of downloads by day+addon name
downloads = {}
# The dates
dates = []

files = sorted(glob.glob('../zap-mgmt-scripts_gh-pages/stats/ext-releases-*'))
# Need an extra day to get the right baseline
files = files[-(days+1):]
# Print out the column definitions
sys.stdout.write('        [\'Add-on\' ')
for file in files[1:]:
  date = file[-15:-5]
  sys.stdout.write(', \'' + date + '\'')
  dates.append(date)
sys.stdout.write('],\n')

for file in files:
  date = file[-15:-5]
  with open(file) as stats_file:
    stats = json.load(stats_file)

  for stat in stats:
    if (stat['tag_name'] == TAG):
      assets = {}
      for asset in stat['assets']:
        name = asset['name']
        count = asset['download_count']
        if (name in counts):
          assets[name] = (count - counts[name])
          if (name in max):
            if (assets[name] > max[name]):
              # new max
              max[name] = assets[name]
          else:
            # first one
            max[name] = assets[name]
        else:
          # Baseline
          assets[name] = count
        counts[name] = count
        downloads[date + '-' + name] = assets[name]

# Work out the top downloads 
top = sorted(max.items(), key=lambda x: (x[1],x[0]), reverse=True)
top = top[:20]
for addon in top:
  name = addon[0]
  sys.stdout.write('        [\'' + name + '\'')
  for date in dates:
    sys.stdout.write(', ')
    if (date + '-' + name in downloads):
      sys.stdout.write(str(downloads[date + '-' + name]))
    else:
      sys.stdout.write('0')
  sys.stdout.write('],\n')

