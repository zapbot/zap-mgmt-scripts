'''
Script for collecting and processing the ZAP service stats
'''
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

day_raw_file = utils.basedir() + 'cfu/raw/cfu-day-ver-' + today_str + '.csv'
mon_raw_file = utils.basedir() + 'cfu/raw/cfu-mon-ver-' + this_mon_str + '.csv'

day_proc_file = utils.basedir() + 'bitly/daily/cfu-day-ver-' + today_str + '.csv'
mon_proc_file = utils.basedir() + 'bitly/monthly/cfu-mon-ver-' + this_mon_str + '.csv'

def aws_athena_query(query):
    print('AWS Athena query: ' + query)
    process = subprocess.run(
        ["aws", "athena", "start-query-execution", 
            "--query-string", query, 
            "--work-group", "project-zap"],
        universal_newlines = True, stdout = subprocess.PIPE)
    res = json.loads(process.stdout)
    if aws_qei in res:
        return res[aws_qei]
    return None

def aws_athena_query_result(id):
    print('AWS Athena query result: ' + id)
    process = subprocess.run(
        ["aws", "athena", "get-query-execution", 
            "--query-execution-id", id],
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
        for _ in range(20):
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

def collect():
    # Requests by day and version
    aws_athena_query_to_file(
        'SELECT day, zapVersion, count(*) as count FROM "zap-cfu-DS"."default"."zap-cfu" WHERE day = \'' + today_str + '\' GROUP BY day, zapVersion', 
        day_raw_file)
    
    # Requests by month and version
    if not os.path.isfile(mon_raw_file):
        # For historical reasons the monthly stats are collected on the 2nd of the next month
        aws_athena_query_to_file(
            'SELECT \'' + this_mon_str + '-02\', zapVersion, count(*) as count FROM "zap-cfu-DS"."default"."zap-cfu" WHERE day LIKE \'' + last_mon_str + '-%\' GROUP BY zapVersion', 
            mon_raw_file)
    

def daily():
    # The raw files are mostly good but they need all of the double quotes stripping out
    
    # Requests by day and version
    copy_without_quotes(day_raw_file, day_proc_file)

    # Requests by month and version
    if not os.path.isfile(mon_proc_file):
        copy_without_quotes(mon_raw_file, mon_proc_file)

def website():
    # All handled by the bitly script
    pass

if __name__ == '__main__':
    if len(sys.argv) == 2:
        fn = sys.argv[1]
        if fn in globals():
            globals()[sys.argv[1]]()
