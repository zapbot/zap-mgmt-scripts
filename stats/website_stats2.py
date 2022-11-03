'''
Script for updating the website stats from the new services
'''
import calendar
import csv
import utils
import glob
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta

aws_region = "us-east-2"
aws_qei = "QueryExecutionId";

# Dates and their string versions
today = datetime.now()
yesterday = today - timedelta(1)
today_str = datetime.strftime(yesterday, '%Y-%m-%d')
this_mon_str = datetime.strftime(today, '%Y-%m')
first = today.replace(day=1)
last_month = first - timedelta(days=1)
last_mon_str = datetime.strftime(last_month, '%Y-%m')
last_mon_full_str = datetime.strftime(last_month, '%B %Y')

day_raw_file = utils.basedir() + 'cfu/raw/cfu-day-ver-' + today_str + '.csv'
mon_raw_file = utils.basedir() + 'cfu/raw/cfu-mon-ver-' + this_mon_str + '.csv'

day_proc_file = utils.basedir() + 'bitly/daily/cfu-day-ver-' + today_str + '.csv'
mon_proc_file = utils.basedir() + 'bitly/monthly/cfu-mon-ver-' + this_mon_str + '.csv'

last_mon_sql = 'timestamp BETWEEN CAST(\'' + last_mon_str + '-01 00:00:00\' AS timestamp) AND CAST(\'' + this_mon_str + '-01 00:00:00\' AS timestamp)'

def aws_athena_query(query):
    print('AWS Athena query: ' + query)
    process = subprocess.run(
        ["aws", "athena", "start-query-execution", 
            "--query-string", query, 
            "--work-group", "project-zap",
            "--region", aws_region],
        universal_newlines = True, stdout = subprocess.PIPE)
    res = json.loads(process.stdout)
    if aws_qei in res:
        return res[aws_qei]
    return None

def aws_athena_query_result(id):
    print('AWS Athena query result: ' + id)
    process = subprocess.run(
        ["aws", "athena", "get-query-execution", 
            "--query-execution-id", id,
            "--region", aws_region],
        universal_newlines = True, stdout = subprocess.PIPE)
    #print(process.stdout)
    return json.loads(process.stdout)

def aws_s3_copy(source, dest):
    print('AWS S3 copy: ' + source + ' ' + dest)
    process = subprocess.run(
        ["aws", "s3", "cp", source, dest],
        universal_newlines = True, stdout = subprocess.PIPE)
    print(process.stdout)

def aws_athena_query_to_file(query, file):
    qid = aws_athena_query(query)
    if qid is not None:
        # Loop polling for the result
        for _ in range(100):
            res = aws_athena_query_result(qid)
            if res['QueryExecution']['Status']['State'] == "FAILED":
                print(res)
                break
            if res['QueryExecution']['Status']['State'] == "SUCCEEDED":
                aws_s3_copy(res['QueryExecution']['ResultConfiguration']['OutputLocation'], file)
                break
            time.sleep(5)


def copy_without_quotes(source, dest) :
    print ('Copying ' + source + ' to ' + dest + ' minus quotes')
    with open(source, 'r') as fs, open(dest, 'w') as fd:
        for line in fs:
            fd.write(line.replace('"', '').replace("'", ""))

def format_int_str(n):
    return str("{:,}".format(int(n.replace('"', ''))))

def count_stat_query(stat):
    return 'SELECT stat, "sum"(value) sum FROM "project_zap_stats"."tel_scanrules" WHERE ' + last_mon_sql + ' AND stat = \'' + stat + '\' GROUP BY stat '

def count_stat_like_query(stat):
    return 'SELECT "sum"(value) sum FROM "project_zap_stats"."tel_scanrules" WHERE ' + last_mon_sql + ' AND stat LIKE \'' + stat + '\''

def gen_headline_file():
    outfile = utils.websitedir() + 'site/data/charts/headline.yaml'
    tempfile = "tempfile.tmp"
    with open(outfile, 'w') as f:
        print('month: ' + last_mon_full_str, file=f)

        # Count of ZAP starts
        aws_athena_query_to_file(
            'SELECT "count"(*) count FROM "project_zap_stats"."zap_news" WHERE ' + last_mon_sql, tempfile)
        if os.path.isfile(tempfile):
            with open(tempfile) as file:
                lines = file.readlines()
                print('zap_runs: ' + format_int_str(lines[1]), file=f)

        # Count of ascan runs
        aws_athena_query_to_file(count_stat_query('stats.ascan.started'), tempfile)
        if os.path.isfile(tempfile):
            with open(tempfile) as file:
                lines = file.readlines()
                # Format will be stats.ascan.started,452714
                print('zap_ascans: ' + format_int_str(lines[1].split(',')[1]), file=f)

        # Count of alerts raised
        aws_athena_query_to_file(count_stat_like_query('stats.%.alerts'), tempfile)
        if os.path.isfile(tempfile):
            with open(tempfile) as file:
                lines = file.readlines()
                # Format will be stats.ascan.started,452714
                print('zap_alerts: ' + format_int_str(lines[1]), file=f)

        # Count of attacks
        aws_athena_query_to_file(count_stat_query('stats.ascan.urls'), tempfile)
        if os.path.isfile(tempfile):
            with open(tempfile) as file:
                lines = file.readlines()
                # Format will be stats.ascan.urls,452714
                print('zap_attacks: ' + format_int_str(lines[1].split(',')[1]), file=f)

def gen_json_file(filename, title, description, query):
    outfile = utils.websitedir() + 'site/data/charts/' + filename
    print(outfile)
    tempfile = "tempfile.tmp"
    aws_athena_query_to_file(query, tempfile)
    if os.path.isfile(tempfile):
        with open(tempfile) as file:
            lines = file.readlines()

    with open(outfile, 'w') as f:
        print('{', file=f)
        print("  \"title\": \"" + title + "\",", file=f)
        print("  \"description\": \"" + description + "\",", file=f)
        print("  \"data\": [", end='', file=f)
        first = True
        for line in lines:
            kv = line.split(',')
            key = kv[0]
            if (key == '""'):
                key = '"None"'
            value = kv[1].strip()
            if not first:
                print(',', end='', file=f)
                value = value.replace('"', '')
            else:
                first = False
            print("\n    [" + key + ', ' + value + "]", end='', file=f)
        print("\n  ]", file=f)
        print("}", file=f)

def gen_top_addons_file():
    outfile = utils.websitedir() + 'site/data/charts/top_addons_last_month.yaml'
    tempfile = "tempfile.tmp"
    with open(outfile, 'w') as f:
        print('---', file=f)

        aws_athena_query_to_file(
            'SELECT "addon", "count"(*) count FROM "project_zap_stats"."tel_addons" WHERE ' + last_mon_sql +
            ' and aotype = \'opt\' GROUP BY addon ORDER BY count DESC limit 20', tempfile)
        if os.path.isfile(tempfile):
            first = True
            with open(tempfile) as file:
                lines = file.readlines()
                for line in lines:
                    if first:
                        first = False
                    else:
                        print('- id: ' + line.split(',')[0], file=f)

def gen_top_fps_file():
    outfile = utils.websitedir() + 'site/data/charts/top_false_positives_last_month.yaml'
    tempfile = "tempfile.tmp"
    with open(outfile, 'w') as f:
        print('---', file=f)

        aws_athena_query_to_file(
            'SELECT stat, "substr"(stat, 19, ("length"(stat) - 26)) pluginId, alerts.name, alerts.status, alerts.type, "sum"(value) count ' +
            'FROM ("project_zap_stats"."tel_therest" ' +
            'INNER JOIN "project_zap_stats"."alerts" ON (alerts.pluginId = CAST("substr"(tel_therest.stat, 19, ("length"(stat) - 26)) AS integer))) ' +
            'WHERE (' + last_mon_sql + ' AND (stat LIKE \'stats.alertFilter%-1\')) ' +
            'GROUP BY stat, alerts.name, alerts.status, alerts.type ' +
            'ORDER BY count DESC LIMIT 20', tempfile)
        if os.path.isfile(tempfile):
            first = True
            with open(tempfile) as file:
                lines = file.readlines()
                for line in lines:
                    if first:
                        first = False
                    else:
                        vals = line.split(',')
                        print('- id: ' + vals[1].replace('"', ''), file=f)
                        print('  name: ' + vals[2], file=f)
                        print('  status: ' + vals[3], file=f)
                        print('  type: ' + vals[4], file=f)

def gen_top_ascan_rules_file():
    outfile = utils.websitedir() + 'site/data/charts/top_ascan_rules_last_month.yaml'
    tempfile = "tempfile.tmp"
    with open(outfile, 'w') as f:
        print('---', file=f)
        aws_athena_query_to_file(
            'select * from "project_zap_stats"."ascan_combined_stats" order by alert_count desc limit 30', tempfile)
        if os.path.isfile(tempfile):
            first = True
            with open(tempfile) as file:
                lines = file.readlines()
                for line in lines:
                    if first:
                        first = False
                    else:
                        vals = line.split(',')
                        
                        fps_pc = vals[5].replace('"', '')
                        if fps_pc == '':
                            fps_pc = 0
                        fps_pc = float(fps_pc) / 1000
                        
                        print('- id: ' + vals[0].replace('"', ''), file=f)
                        print('  name: ' + vals[1], file=f)
                        print('  status: ' + vals[2], file=f) # Capitalise?
                        print('  alerts: ' + vals[3], file=f)
                        print('  fps: ' + str(fps_pc), file=f)
                        print('  num: ' + vals[6].replace('"', ''), file=f)
                        print('  time: ' + vals[8].replace('"', ''), file=f)

gen_headline_file()

gen_json_file(
    "countries-last-month.json",
    "News Pings by Country in " + last_mon_full_str, 
    "The number of News pings from ZAP by country in " + last_mon_full_str, 
    'SELECT "country" Country, "count"(*) Count FROM "project_zap_stats"."zap_news" WHERE ' +
    last_mon_sql + ' GROUP BY country ORDER BY count DESC limit 20')

gen_json_file(
    "countries-desktop-last-month.json",
    "Desktop News Pings by Country in " + last_mon_full_str, 
    "The number of News pings from ZAP Desktops by country in " + last_mon_full_str, 
    'SELECT "country" Country, "count"(*) Count FROM "project_zap_stats"."zap_news" WHERE ' +
    last_mon_sql + ' and "zaptype" = \'desktop\' GROUP BY country ORDER BY count DESC limit 20')

gen_json_file(
    "os-last-month.json",
    "News Pings by OS in " + last_mon_full_str, 
    "The number of News pings from ZAP by OS in " + last_mon_full_str, 
    'SELECT "os" OS, "count"(*) Count FROM "project_zap_stats"."zap_news" WHERE ' +
    last_mon_sql + ' GROUP BY os ORDER BY count DESC limit 20')

gen_json_file(
    "os-desktop-last-month.json",
    "Desktop News Pings by OS in " + last_mon_full_str, 
    "The number of News pings from ZAP Desktops by OS in " + last_mon_full_str, 
    'SELECT "os" OS, "count"(*) Count FROM "project_zap_stats"."zap_news" WHERE ' +
    last_mon_sql + '  and "zaptype" = \'desktop\' GROUP BY os ORDER BY count DESC limit 20')

gen_json_file(
    "zaptype-last-month.json",
    "News Pings by ZAP Run Type in " + last_mon_full_str, 
    "The number of News pings from ZAP by run type in " + last_mon_full_str, 
    'SELECT "zaptype" ZAPtype, "count"(*) Count FROM "project_zap_stats"."zap_news" WHERE ' +
    last_mon_sql + ' GROUP BY zaptype ORDER BY count DESC limit 20')

gen_json_file(
    "container-last-month.json",
    "News Pings by Container in " + last_mon_full_str, 
    "The number of News pings from ZAP by container in " + last_mon_full_str, 
    'SELECT "container" Container, "count"(*) Count FROM "project_zap_stats"."zap_news" WHERE ' +
    last_mon_sql + ' GROUP BY container ORDER BY count DESC limit 20')

gen_top_addons_file()

gen_top_fps_file()

gen_top_ascan_rules_file()
