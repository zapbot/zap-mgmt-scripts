'''
Post process the telemetry stats

The script expects a 'telemetry/raw' directory containing raw telemetry data.
It processes any files underneath this directory creating new files with the same hierarchy but different root directories:
    raw/        The unprocessed files, which it will move to 'processed'
    env/        The common environmental attributes
    addons/     Add-on related data
    scanrules/  Scan rule related data
    therest/    The remaining stats
    processed/  The processed files

This procedure means that we only need to sync a relatively small number of unprocessed files rather than an ever increasing number.

'''

import json
import os

common_atts = ['day', 'telUuid', 'timestamp', 'uuid']
env_atts = ['container', 'country', 'ipaddress', 'javaVersion', 'memory', 'mode', 'os', 'osVersion', 'locale', 'telIndex', 'teltype', 'ttl', 'uptime', 'zapType', 'zapVersion']
std_addons = ['alertFilters', 'automation', 'ascanrules', 'bruteforce', 'callhome', 'coreLang', 'commonlib', 'diff', 'directorylistv1', 'domxss', 'encoder', 'formhandler', 'fuzz', 'gettingStarted', 'graaljs', 'graphql', 'help', 'hud', 'importurls', 'invoke', 'network', 'oast', 'onlineMenu', 'openapi', 'pscanrules', 'quickstart', 'replacer', 'reports', 'retest', 'retire', 'reveal', 'saverawmessage', 'savexmlmessage', 'scripts', 'selenium', 'soap', 'spiderAjax', 'tips', 'webdriverlinux', 'webdrivermacos', 'webdriverwindows', 'websocket', 'zest']

def create_parent_dirs(filename):
    os.makedirs(os.path.dirname(filename), exist_ok=True)

def process_data(filename, data):
    addon_dict = {}
    common_dict = {}
    env_dict = {}
    scanrule_dict = {}
    therest_dict = {}
    teltype = data['teltype']
    for attribute, value in data.items():
        if attribute in common_atts:
            common_dict[attribute] = value
            env_dict[attribute] = value
        elif attribute in env_atts:
            env_dict[attribute] = value
        elif teltype == 'add-ons':
            addon_dict[attribute] = value
        elif attribute.startswith('stats.ascan.') or attribute.startswith('stats.pscan.'):
            scanrule_dict[attribute] = value
        else:
            therest_dict[attribute] = value

    # Env file
    env_filename = filename.replace('telemetry/raw', 'telemetry/env')
    create_parent_dirs(env_filename)
    with open(env_filename, "a") as ef:
        ef.write(json.dumps(env_dict))
        ef.write('\n')

    # Add-ons file
    for attribute, value in addon_dict.items():
        ao_dict = common_dict.copy()
        ao_dict['addon'] = attribute
        ao_dict['version'] = value
        if attribute in std_addons:
            ao_dict['aotype'] = 'core'
        else:
            ao_dict['aotype'] = 'opt'
        # Append to the addons file...
        ao_filename = filename.replace('telemetry/raw', 'telemetry/addons')
        create_parent_dirs(ao_filename)
        # print('Writing to ' + ao_filename)
        with open(ao_filename, "a") as af:
            af.write(json.dumps(ao_dict))
            af.write('\n')

    # Scan rules file
    for attribute, value in scanrule_dict.items():
        sr_dict = common_dict.copy()
        sr_dict['stat'] = attribute
        sr_dict['value'] = value
        sr_filename = filename.replace('telemetry/raw', 'telemetry/scanrules')
        create_parent_dirs(sr_filename)
        # print('Writing to ' + ao_filename)
        with open(sr_filename, "a") as sf:
            sf.write(json.dumps(sr_dict))
            sf.write('\n')

    # The rest file
    for attribute, value in therest_dict.items():
        tr_dict = common_dict.copy()
        tr_dict['stat'] = attribute
        tr_dict['value'] = value
        tr_filename = filename.replace('telemetry/raw', 'telemetry/therest')
        create_parent_dirs(tr_filename)
        # print('Writing to ' + ao_filename)
        with open(tr_filename, "a") as rf:
            rf.write(json.dumps(tr_dict))
            rf.write('\n')

for root, dirs, files in os.walk('telemetry/raw'):
    for file in files:
        filename = os.path.join(root, file)
        processed_filename = filename.replace('telemetry/raw', 'telemetry/processed')
        create_parent_dirs(processed_filename)
        if os.path.isfile(filename.replace('telemetry/raw', 'telemetry/env')):
            # print('Already processed ' + root + ' ' + file)
            os.rename(filename, processed_filename)
            continue
        print('Processing ' + root + ' ' + file)
            
        with open(filename, "r") as tf:
            for line in tf.readlines():
                data = json.loads(line)
                process_data(filename, data)

        os.rename(filename, processed_filename)
