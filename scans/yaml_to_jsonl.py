#!/usr/bin/env python3
"""Convert ZAP scan result YAML files to JSON Lines for S3/Athena storage.

Usage: yaml_to_jsonl.py <date> <scan> <yaml_file> [<yaml_file> ...]
Output: JSON Lines to stdout, one record per tested path.
"""
import json
import sys
import yaml


def convert(date, scan, yaml_path):
    with open(yaml_path) as f:
        data = yaml.safe_load(f)
    if 'section' not in data:
        return
    section = data['section']
    for detail in data.get('details', []):
        record = {
            'date': date,
            'scan': scan,
            'section': section,
            'path': detail['path'],
            'result': detail['result'],
            'rules': detail.get('rules', []),
        }
        print(json.dumps(record))


if __name__ == '__main__':
    date = sys.argv[1]
    scan = sys.argv[2]
    for yaml_path in sys.argv[3:]:
        convert(date, scan, yaml_path)
