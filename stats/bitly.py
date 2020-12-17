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
