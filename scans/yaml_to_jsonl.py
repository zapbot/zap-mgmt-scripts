#!/usr/bin/env python3
"""Convert ZAP scan result YAML files to JSON Lines for S3/Athena storage.

Usage: yaml_to_jsonl.py <date> <scan> <yaml_file> [<yaml_file> ...]
Output: JSON Lines to stdout, one record per tested path.
"""
import json
import os
import sys
import yaml


# Keys that are metadata, not pass/fail tool or rule results
_NON_RESULT_KEYS = {'path', 'scheme', 'title', 'any'}


def convert(date, scan, yaml_path):
    with open(yaml_path) as f:
        data = yaml.safe_load(f)
    if 'section' not in data:
        return
    section_key = os.path.splitext(os.path.basename(yaml_path))[0]
    section = data['section']
    url = data.get('url', data.get('target', ''))
    for detail in data.get('details', []):
        if 'result' in detail:
            # Standard format (wavsep, firingrange): explicit result + rules list
            path = detail['path']
            result = detail['result']
            rules = detail.get('rules', [])
        else:
            # Dynamic-key format (crawlground, SSTI): per-tool/rule keys with
            # 'Pass'/'FAIL' values; path may be under 'path' or 'title'
            path = detail.get('path') or detail.get('title', '')
            scored = {k: v for k, v in detail.items() if k not in _NON_RESULT_KEYS}
            rules = [k for k, v in scored.items() if v == 'Pass']
            result = 'Pass' if rules else 'FAIL'
        record = {
            'date': date,
            'scan': scan,
            'section_key': section_key,
            'section': section,
            'url': url,
            'path': path,
            'result': result,
            'rules': rules,
        }
        print(json.dumps(record))


if __name__ == '__main__':
    date = sys.argv[1]
    scan = sys.argv[2]
    for yaml_path in sys.argv[3:]:
        convert(date, scan, yaml_path)
