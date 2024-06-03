'''
Script for collecting and processing the ZAP GHCR stats
'''
import csv
import glob
import json
import os
import re
import utils

images = {
    "zaproxy",
    }

base = 'https://github.com/zaproxy/zaproxy/pkgs/container/'

def collect():
    for image in images:
        utils.download_to_file(base + image, utils.basedir() + "ghcr/raw/" + utils.today() + '-' + image + ".html")

def find_count(html):
    ''' The count is currently reported via html like this:
        <div class="lh-condensed d-flex flex-column flex-items-baseline pr-1">
          <span class="d-block color-fg-muted text-small mb-1">Total downloads</span>
          <h3 title="670091">670K</h3>
        </div>
    '''
    m = re.search("<h3 title=\"(.*)\".*[KM]</h3>", html)
    if m:
        try:
            return int(m.group(1))
        except  ValueError:
            pass
    return -1

def daily():
    files = sorted(glob.glob(utils.basedir() + 'ghcr/raw/*.html'))
    created = set()
    last_monthly_totals = {}
    last_day_totals = {}
    monthly_files_to_write = set()
    for file in files:
        with open(file) as stats_file:
            date_str = os.path.basename(stats_file.name)[:10]
            image = os.path.basename(stats_file.name)[11:-5]
            data = stats_file.read()
            total = find_count(data)

            is_monthly = date_str.endswith('-01')
            
            if is_monthly:
                monthly_file = utils.basedir() + 'ghcr/monthly/' + date_str + '.csv'
                if not os.path.exists(monthly_file):
                    with open(monthly_file, "a") as f:
                        f.write('date,image,total,increase\n')
                        monthly_files_to_write.add(date_str)
                        print('Created ' + monthly_file)
                if date_str in monthly_files_to_write:
                    with open(monthly_file, "a") as f:
                        if image in last_monthly_totals:
                            f.write(date_str + ',' + image + ',' + str(total) + ',' + str(total - last_monthly_totals[image]) + "\n")
                        else:
                            f.write(date_str + ',' + image + ',' + str(total) + ',' + str(total) + "\n")
                last_monthly_totals[image] = total

            if image in last_day_totals:
                daily_file = utils.basedir() + 'ghcr/daily/' + date_str + '.csv'
                if not os.path.exists(daily_file):
                    with open(daily_file, "a") as f:
                        f.write('date,image,total,increase\n')
                    created.add(date_str)
                    print('Created ' + daily_file)
                if date_str in created:
                    with open(daily_file, "a") as f:
                        f.write(date_str + ',' + image + ',' + str(total) + ',' + str(total - last_day_totals[image]) + "\n")
            last_day_totals[image] = total


def website():
    # This is handled in the docker.py file
    pass
    
