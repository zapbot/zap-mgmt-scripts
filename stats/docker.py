'''
Script for collecting and processing the ZAP docker stats
'''
import glob
import json
import os
import utils

urls = {
    "stable": "https://registry.hub.docker.com/v2/repositories/owasp/zap2docker-stable/",
    "weekly": "https://registry.hub.docker.com/v2/repositories/owasp/zap2docker-weekly/",
    "live": "https://registry.hub.docker.com/v2/repositories/owasp/zap2docker-live/",
    "bare": "https://registry.hub.docker.com/v2/repositories/owasp/zap2docker-bare/",
    }

def collect():
    for key, url in urls.items():
        utils.download_to_file(url, utils.basedir() + "docker/raw/" + utils.today() + '-' + key + ".json")

def daily():
    files = sorted(glob.glob(utils.basedir() + 'docker/raw/*.json'))
    created = set()
    last_monthly_totals = {}
    last_day_totals = {}
    monthly_files_to_write = set()
    for file in files:
        with open(file) as stats_file:
            stats = json.load(stats_file)
            link = os.path.basename(stats_file.name)[20:-5]
            date_str = os.path.basename(stats_file.name)[:10]
            image = stats['name']
            total = stats['pull_count']

            is_monthly = date_str.endswith('-01')
            if is_monthly:
                if image in last_monthly_totals:
                    monthly_file = utils.basedir() + 'docker/monthly/' + date_str + '.csv'
                    if not os.path.exists(monthly_file):
                        with open(monthly_file, "a") as f:
                            f.write('date,image,total,increase,stars\n')
                            monthly_files_to_write.add(date_str)
                            print('Created ' + monthly_file)
                    if date_str in monthly_files_to_write:
                        with open(monthly_file, "a") as f:
                            f.write(date_str + ',' + image + ',' + str(total) + ',' + str(total - last_monthly_totals[image]) + ',' + str(stats['star_count']) + "\n")
                last_monthly_totals[image] = total

            if image in last_day_totals:
                daily_file = utils.basedir() + 'docker/daily/' + date_str + '.csv'
                if not os.path.exists(daily_file):
                    with open(daily_file, "a") as f:
                        f.write('date,image,total,increase,stars\n')
                    created.add(date_str)
                    print('Created ' + daily_file)
                if date_str in created:
                    with open(daily_file, "a") as f:
                        f.write(date_str + ',' + image + ',' + str(total) + ',' + str(total - last_day_totals[image]) + ',' + str(stats['star_count']) + "\n")
            last_day_totals[image] = total
