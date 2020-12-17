'''
Script for collecting and processing the ZAP github stats
'''
import utils
import glob
import json
import os
import sys

tags = [
    "v2.10.0",
    "v2.9.0",
    "v2.8.0",
    ]

mappings = {
  "core": "core",
  "crossplatform": "cross",
  "linux": "linux",
  "unix": "unix",
  "deb": "deb",
  "dmg": "mac",
  "windows-x32": "win32",
  "windows.exe": "win64",
}

github_api = "https://api.github.com/repos/zaproxy/zaproxy/releases/tags/"

def collect():
    for tag in tags:
        utils.download_to_file(github_api + tag, utils.basedir() + "downloads/raw/" + utils.today() + '-' + tag + ".json")

def daily():
    # Process the download stats
    counts = {}
    assets = {}
    daily_files_to_write = set()
    monthly_files_to_write = set()
    files = sorted(glob.glob(utils.basedir() + "downloads/raw/*.json"))
    last_monthly_totals = {}
    for file in files:
        with open(file) as stats_file:
            stats = json.load(stats_file)
            date_str = os.path.basename(stats_file.name)[:10]
            daily_file = utils.basedir() + 'downloads/daily/' + date_str + '.csv'
            # Todays stats will be incomplete as this is run at the start of the day
            if not os.path.exists(daily_file) and not date_str == utils.today():
                daily_files_to_write.add(date_str)
                with open(daily_file, "a") as f:
                    print('Creating ' + daily_file)
                    f.write('date,version,name,tag,downloads\n')
                    
            is_monthly = date_str.endswith('-01')
            daily_total = 0
            for asset in stats['assets']:
                tag = stats['name']
                name = asset['name']
                count = asset['download_count']
                if (name in counts):
                    # Ignore negative numbers - can happen when files are replaced
                    old_count = counts[name]
                else:
                    old_count = 0
                if (name in counts):
                    # Ignore negative numbers - can happen when files are replaced
                    assets[name] = max((count - counts[name]), 0)
                else:
                    assets[name] = count
                counts[name] = count
                if is_monthly:
                    daily_total += counts[name]
                mapping = "Unknown"
                for m in mappings:
                    if m in name.lower():
                        mapping = mappings[m]
                        break
                
                if old_count > 0:
                    # There can be multiple raw files with the same date, ie one per tag
                    if date_str in daily_files_to_write:
                        with open(daily_file, "a") as f:
                            f.write(date_str + ',' +  tag + ',' + asset['name'] + ',' + mapping + ',' + str(assets[name]) + '\n')

            if is_monthly:
                if tag in last_monthly_totals:
                    monthly_file = utils.basedir() + 'downloads/monthly/' + date_str + '.csv'
                    if not os.path.exists(monthly_file):
                        monthly_files_to_write.add(date_str)
                        with open(monthly_file, "a") as f:
                            print('Creating ' + monthly_file)
                            f.write('date,version,total,downloads\n')
                    # There can be multiple raw files with the same date, ie one per tag
                    if date_str in monthly_files_to_write:
                        with open(monthly_file, "a") as f:
                            f.write(date_str + ',' +  tag + ',' + str(daily_total) + ',' + str(daily_total - last_monthly_totals[tag]))

                last_monthly_totals[tag] = daily_total
