'''
Script for collecting and processing the ZAP bitly stats
'''
import glob
import json
import os
import sys
import utils

links = [
    "owaspzap-2-9-0d", \
    "owaspzap-2-9-0", \
    "owaspzap-2-8-0", \
    "owaspzap-2-7-0", \
    "owaspzap-2-6-0", \
    "owaspzap-2-5-0", \
    "owaspzap-2-4-3", \
    "owaspzap-devw", \
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

bitly_api = "https://api-ssl.bitly.com/v4/bitlinks/bit.ly/{{LINK}}/clicks?unit=day&units=-1&size=7"

def collect():
    headers = {'Authorization': 'Bearer ' + os.getenv('BITLY_TOKEN')}
    for link in links:
        utils.download_to_file(bitly_api.replace('{{LINK}}', link), utils.basedir() + "bitly/raw/" + utils.today() + '-' + link + ".json", headers)

def daily():
    files = sorted(glob.glob(utils.basedir() + 'bitly/raw/*.json'))
    created = set()
    first_month = ""
    last_monthly_totals = {}
    monthly_files_to_write = set()
    for file in files:
        with open(file) as stats_file:
            stats = json.load(stats_file)
            link = os.path.basename(stats_file.name)[20:-5]
            date_collected = os.path.basename(stats_file.name)[:10]
            #print(stats_file.name + ' ' + link + ' ' + date_collected)
            for lc in stats['link_clicks']:
                date_str = lc['date'][:10]
                is_monthly = date_str.endswith('-01')
                if is_monthly:
                    if len(first_month) == 0:
                        first_month = date_str
                    if len(first_month) > 0 and not first_month == date_str:
                        monthly_file = utils.basedir() + 'bitly/monthly/' + date_str + '.csv'
                        if not os.path.exists(monthly_file):
                            with open(monthly_file, "a") as f:
                                f.write('date,link,clicks\n')
                                monthly_files_to_write.add(date_str)
                                print('Created ' + monthly_file)
                        if date_str in monthly_files_to_write:
                            with open(monthly_file, "a") as f:
                                f.write(date_str + ',' + link + ',' + str(last_monthly_totals[link]) + '\n')
                                last_monthly_totals[link] = 0

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

                    # Monthly totals
                    if not link in last_monthly_totals:
                        last_monthly_totals[link] = 0
                    last_monthly_totals[link] += lc['clicks']
