'''
Script for collecting and processing the ZAP docker stats
'''
import csv
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

            is_monthly = date_str.endswith('-01') or date_str == '2021-08-02' # No stats for 2021-08-01 :/
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

def website():
    files = sorted(glob.glob(utils.basedir() + 'docker/monthly/*.csv'))
    outfile = utils.websitedir() + 'site/data/charts/docker.json'
    if not os.path.isfile(outfile):
        print('No existing file: ' + outfile)
        return
    
    images = []
    map = {}
    
    '''
    All files have format: date,image,total,increase,stars
    '''
    
    for file in files:
        with open(file) as monthly_file:
            csv_reader = csv.reader(monthly_file)
            # Ignore the header
            next(csv_reader)
            for row in csv_reader:
                if len(row) > 0:
                    date = row[0]
                    image = row[1]
                    if image.startswith("zap2docker-"):
                        image = image[11:]
                    increase = row[3]
                    if not image in images:
                        images.append(image)
                    if not date in map:
                        map[date] = {}
                    map[date][image] = increase
    
    with open(outfile, 'w') as f:
        print('{', file=f)
        print('  "title": "Docker Pulls",', file=f)
        print('  "description": "Docker pulls since the ZAP Docker images were published.",', file=f)
        print('  "columns": ["Version" ', end='', file=f)
        for l in images:
            print(', "' + l + '"', end='', file=f)
        print('],', file=f)
        print('  "data": [', end='', file=f)
        
        first = True
        for date in sorted(map.keys()):
            if not first:
                print(',', end='', file=f)
            else:
                first = False
            # Monthly stats tend to get recorded as the 2nd even though they really apply to the previous month
            print('\n    ["' + date[:-2] + '01"', end='', file=f)
            for l in images:
                if l in map[date] and len(map[date][l]) > 0:
                    print(', ' + map[date][l], end='', file=f)
                else:
                    print(', 0', end='', file=f)
            print(', ""]', end='', file=f)
        
        print('\n  ]', file=f)
        print('}', file=f)

    print('Updated: ' + outfile)
