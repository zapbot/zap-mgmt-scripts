'''
Script for collecting and processing the ZAP bitly stats
'''
import csv
import datetime
import glob
import json
import os
import sys
import utils

links = [
    "owaspzap-2-11-0d", \
    "owaspzap-2-11-0", \
    "owaspzap-2-10-0d", \
    "owaspzap-2-10-0", \
    "owaspzap-2-9-0d", \
    "owaspzap-2-9-0", \
    "owaspzap-2-8-0", \
    "owaspzap-2-7-0", \
    "owaspzap-2-6-0", \
    "owaspzap-2-5-0", \
    "owaspzap-2-4-3", \
    "owaspzap-devw", \
    "owaspzap-news-2-11", \
    "owaspzap-news-2-10", \
    "owaspzap-news-2-9", \
    "owaspzap-news-2-8", \
    "owaspzap-news-dev", \
    "owaspzap-hud", \
    "owaspzap-hud-tutorial-start", \
    "owaspzap-hud-tutorial-end", \
    "owaspzap-start-2-7", \
    "owaspzap-start-2-6", \
    "owaspzap-start-dev", \
    ]

links_for_country_stats = [
    "owaspzap-2-11-0d", \
    "owaspzap-2-11-0", \
    "owaspzap-news-2-11", \
    "owaspzap-2-10-0d", \
    "owaspzap-2-10-0", \
    "owaspzap-news-2-10", \
    "owaspzap-2-9-0d", \
    "owaspzap-2-9-0", \
    "owaspzap-news-2-9", \
    ]

bitly_clicks_api = "https://api-ssl.bitly.com/v4/bitlinks/bit.ly/{{LINK}}/clicks?unit=day&units=-1&size=7"
bitly_countries_api = "https://api-ssl.bitly.com/v4/bitlinks/bit.ly/{{LINK}}/countries?unit=day&units=1&size=100"

def collect():
    headers = {'Authorization': 'Bearer ' + os.getenv('BITLY_TOKEN')}
    for link in links:
        utils.download_to_file(bitly_clicks_api.replace('{{LINK}}', link), utils.basedir() + "bitly/raw/" + utils.today() + '-' + link + ".json", headers)

    for link_cs in links_for_country_stats:
        utils.download_to_file(bitly_countries_api.replace('{{LINK}}', link_cs), utils.basedir() + "bitly/raw-countries/" + utils.today() + '-' + link_cs + ".json", headers)

def daily():
    files = sorted(glob.glob(utils.basedir() + 'bitly/raw/*.json'))
    created = set()
    for file in files:
        with open(file) as stats_file:
            stats = json.load(stats_file)
            link = os.path.basename(stats_file.name)[20:-5]
            date_collected = os.path.basename(stats_file.name)[:10]
            #print(stats_file.name + ' ' + link + ' ' + date_collected)
            for lc in stats['link_clicks']: # TODO these will be duplicated
                date_str = lc['date'][:10]
                # Stats for the day of collection will probably be incomplete
                if not date_str == date_collected:
                    daily_file = utils.basedir() + 'bitly/daily/' + date_str + '.csv'
                    if not os.path.exists(daily_file):
                        with open(daily_file, "a") as f:
                            f.write('date,link,clicks\n')
                        created.add(date_str)
                        print('Created ' + daily_file)
                    if date_str in created:
                        with open(daily_file, "a") as f:
                            f.write(date_str + ',' + link + ',' + str(lc['clicks']) + '\n')

    # The raw stats contain duplicate days so its easier to work out the monthly stats from the daily ones
    today = datetime.date.today()
    if (today.day > 1):
        first_str = today.replace(day=1).strftime('%Y-%m-%d')
        monthly_file = utils.basedir() + 'bitly/monthly/' + first_str + '.csv'
        if not os.path.exists(monthly_file):
            monthly_totals = {}
            if today.month == 1:
                last_month = today.replace(year = today.year-1).replace(month = 12)
            else:
                last_month = today.replace(month = today.month-1)
            files = sorted(glob.glob(utils.basedir() + 'bitly/daily/' + last_month.strftime('%Y-%m-') + '*.csv'))
            for file in files:
                with open(file) as daily_file:
                    csv_reader = csv.reader(daily_file)
                    # Ignore the header
                    next(csv_reader)
                    for row in csv_reader:
                        link = row[1]
                        clicks = row[2]
                        if not link in monthly_totals:
                            monthly_totals[link] = 0
                        monthly_totals[link] += int(clicks)
            with open(monthly_file, "a") as f:
                f.write('date,link,clicks\n')
                for link in monthly_totals:
                    f.write(utils.today() + ',' + link + "," + str(monthly_totals[link]) + '\n')
            print('Created ' + monthly_file)

def is_cfu(link):
    return link.startswith('2') or link.startswith('devw') or link.startswith('Daily') 

def website():
    '''
    Currently just handling the check for update requests as per is_cfu
    '''
    files = sorted(glob.glob(utils.basedir() + 'bitly/monthly/*.csv'))
    outfile = utils.websitedir() + 'site/data/charts/check-for-updates.json'
    if not os.path.isfile(outfile):
        print('No existing file: ' + outfile)
        return
    links = []
    map = {}
    
    for file in files:
        with open(file) as monthly_file:
            csv_reader = csv.reader(monthly_file)
            # Ignore the header
            next(csv_reader)
            for row in csv_reader:
                date = row[0]
                link = row[1]
                # Handle new CFU service stats
                if link.startswith('D-'):
                    link = 'Daily'
                if "." in link:
                    # This will need to change when ZAP uses the new CFU service
                    continue
                
                if len(row) > 3:
                    clicks = row[3]
                else:
                    clicks = row[2]
                if not link in links:
                    links.append(link)
                if not date in map:
                    map[date] = {}
                    
                if link in map[date]:
                    map[date][link] = str(int(map[date][link]) + int(clicks))
                else:
                    map[date][link] = clicks

    with open(outfile, 'w') as f:
        print('{', file=f)
        print('  "title": "Check for Updates",', file=f)
        print('  "description": "The number of Check for Update requests received per month. From 2.9.0 the suffix \'d\' indicates ZAP is running as a daemon rather than the desktop.",', file=f)
        print('  "columns": ["Version" ', end='', file=f)
        for l in links:
            if is_cfu(l):
                print(', "' + l + '"', end='', file=f)
        print('],', file=f)
        print('  "data": [', end='', file=f)
        
        first = True
        for date in sorted(map.keys()):
            # Monthly stats tend to get recorded as the 2nd even though they really apply to the previous month
            if not first:
                print(',', end='', file=f)
            else:
                first = False
            print('\n    ["' + date[:-2] + '01"', end='', file=f)
            for l in links:
                if is_cfu(l):
                    if l in map[date] and len(map[date][l]) > 0:
                        print(', ' + map[date][l], end='', file=f)
                    else:
                        print(', 0', end='', file=f)
            print(', ""]', end='', file=f)
            
        print('\n  ]', file=f)
        print('}', file=f)

    print('Updated: ' + outfile)

if __name__ == '__main__':
    if len(sys.argv) == 2:
        fn = sys.argv[1]
        if fn in globals():
            globals()[sys.argv[1]]()
