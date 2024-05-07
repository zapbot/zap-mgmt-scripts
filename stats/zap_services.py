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

def convert_file(source, dest) :
    '''
        Old format: date,link,clicks where link is like '2-11-0' (desktop/cmdline) or '2-11-0d' (daemon)
        New format: date,zapVersion,zaptype,count where zaptype is daemon/desktop/cmdline
    '''
    print ('Processing ' + source + ' to ' + dest + ' minus quotes')
    first = True
    with open(source, 'r') as fs, open(dest, 'w') as fd:
        daily = 0
        for line in fs:
            if first:
                fd.write('date,link,clicks\n')
                first = False
            else:
                (date, ver, type, count) = line.replace('"', '').replace("'", "").split(',')
                valid = True
                if ver.startswith('D-'):
                    daily += int(count.strip())
                    dday = date
                    ver = 'Daily'
                elif ver == '2.12.0' or ver == '2.13.0' or ver == '2.14.0' or ver == '2.15.0':  # Will need to change for new releases
                    ver = ver.replace('.', '-')
                    if type == 'daemon':
                        ver = ver + 'd'
                    fd.write(date + ',' + ver + ',' + count)
        if daily > 0:
            fd.write(dday + ',Daily,' + str(daily) + '\n')


def collect():
    # Requests by day and version
    aws_athena_query_to_file(
        'SELECT day, zapVersion, zaptype, count(*) as count FROM "AwsDataCatalog"."project_zap_stats"."zap_cfu" WHERE day = \'' + today_str + '\' GROUP BY day, zapVersion, zaptype', 
        day_raw_file)
    
    # Requests by month and version
    if not os.path.isfile(mon_raw_file):
        # For historical reasons the monthly stats are collected on the 2nd of the next month
        aws_athena_query_to_file(
            'SELECT \'' + this_mon_str + '-02\', zapVersion, zaptype, count(*) as count FROM "AwsDataCatalog"."project_zap_stats"."zap_cfu" WHERE day LIKE \'' + last_mon_str + '-%\' GROUP BY zapVersion, zaptype', 
            mon_raw_file)
    

def daily():
    # The raw files need to be processed to match the 'old' expected format
    
    # Requests by day and version
    convert_file(day_raw_file, day_proc_file)

    # Requests by month and version
    if not os.path.isfile(mon_proc_file):
        convert_file(mon_raw_file, mon_proc_file)

def website():
    # All handled by the bitly script
    pass

if __name__ == '__main__':
    if len(sys.argv) == 2:
        fn = sys.argv[1]
        if fn in globals():
            globals()[sys.argv[1]]()
