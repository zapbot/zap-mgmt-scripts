'''
Script for processing the ZAP Google Group stats
'''
import csv
import glob
import json
import os
import utils


def collect():
    # These are collected manually
    pass

def daily():
    # These are processed manually
    pass

def website():
    files = sorted(glob.glob(utils.basedir() + 'groups/monthly/*.csv'))
    outfile = utils.websitedir() + 'site/data/charts/user-group.json'
    if not os.path.isfile(outfile):
        print('No existing file: ' + outfile)
        return
    
    map = {}
    stats = ['messages', 'threads']
    
    '''
    All files have format: date,name,messages,threads
    '''
    
    for file in files:
        with open(file) as monthly_file:
            csv_reader = csv.reader(monthly_file)
            # Ignore the header
            next(csv_reader)
            for row in csv_reader:
                if len(row) > 0:
                    date = row[0]
                    name = row[1]
                    if name == 'zaproxy-users':
                        messages = row[2]
                        threads = row[3]
                        if not date in map:
                            map[date] = {}
                        map[date]['messages'] = messages
                        map[date]['threads'] = threads

    
    with open(outfile, 'w') as f:
        print('{', file=f)
        print('  "title": "User Group",', file=f)
        print('  "description": "Messages and threads since the group was created.",', file=f)
        print('  "columns": ["Date" , "Messages", "Threads"],', file=f)
        print('  "data": [', end='', file=f)
        
        first = True
        for date in sorted(map.keys()):
            if not first:
                print(',', end='', file=f)
            else:
                first = False
            # Monthly stats tend to get recorded as the 2nd even though they really apply to the previous month
            print('\n    ["' + date[:-2] + '01"', end='', file=f)
            for l in stats:
                if l in map[date] and len(map[date][l]) > 0:
                    print(', ' + map[date][l], end='', file=f)
                else:
                    print(', 0', end='', file=f)
            print(', ""]', end='', file=f)
        
        print('\n  ]', file=f)
        print('}', file=f)

    print('Updated: ' + outfile)
