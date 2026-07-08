#!/usr/bin/env python3
"""Generate per-section YAML files for the website from historical S3 JSONL data.

Reads JSONL files (one per day, named YYYY-MM-DD.jsonl) from --data-dir,
computes rolling pass rates per path/rule, and writes per-section YAML files
to --output-dir replacing the daily snapshot files.

Usage:
  generate-scan-stats.py --data-dir <dir> --output-dir <dir>
                         [--days N] [--compare-days N]

  --days N          Current window in days (default: 7)
  --compare-days N  Previous window size for trend arrows (default: same as --days;
                    use 0 to disable trend)
"""
import argparse
import json
import os
from collections import defaultdict
from datetime import date, timedelta

import yaml


def parse_args():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--data-dir', required=True,
                   help='Directory containing YYYY-MM-DD.jsonl files')
    p.add_argument('--output-dir', required=True,
                   help='Directory to write per-section YAML files')
    p.add_argument('--days', type=int, default=7,
                   help='Current window size in days (default: 7)')
    p.add_argument('--compare-days', type=int, default=None,
                   help='Previous window size for trend (default: same as --days)')
    p.add_argument('--end-date', default=None,
                   help='Last date (inclusive) of current window, YYYY-MM-DD (default: yesterday)')
    return p.parse_args()


def load_records(data_dir, start_date, num_days):
    """Load all JSONL records for a num_days window starting at start_date.

    Returns (records, days_with_data) where days_with_data is the actual number
    of days in the window that had data files (used as the score denominator).
    """
    records = []
    days_with_data = 0
    for i in range(num_days):
        path = os.path.join(data_dir, f'{(start_date + timedelta(days=i)).isoformat()}.jsonl')
        if os.path.exists(path):
            days_with_data += 1
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        records.append(json.loads(line))
    return records, days_with_data


def index_records(records):
    """
    Build lookup structures from a list of records.

    Returns:
      sections: {section_key -> {name, url}}
      firing:   {section_key -> {path -> {rule -> set(dates)}}}
      paths:    {section_key -> ordered list of paths (insertion order)}
    """
    sections = {}
    firing = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))
    path_order = defaultdict(dict)  # section_key -> {path: None} (ordered set)

    for r in records:
        key = r.get('section_key')
        if not key or r.get('result') == 'Broken':
            continue
        if key not in sections:
            sections[key] = {'name': r.get('section', key), 'url': r.get('url', '')}
        path = r['path']
        path_order[key][path] = None
        for rule in r.get('rules', []):
            firing[key][path][rule].add(r['date'])

    return sections, firing, path_order


def fmt_score(rate):
    if rate >= 1.0:
        return 'Pass'
    if rate <= 0.0:
        return 'Fail'
    return f'{round(rate * 100)}%'


def fmt_pct(rate):
    return f'{round(rate * 100)}%'


def get_trend(curr_rate, prev_rate):
    """Returns (trend, prev_score_str) or (None, None) if no comparison."""
    if prev_rate is None:
        return None, None
    diff = curr_rate - prev_rate
    if diff > 0.05:
        return 'up', fmt_score(prev_rate)
    if diff < -0.05:
        return 'down', fmt_score(prev_rate)
    return 'stable', fmt_score(prev_rate)


def build_section_yaml(sec_info, curr_firing, prev_firing, path_order,
                       curr_window, prev_window):
    """
    Build the YAML dict for one section.

    curr_firing / prev_firing: {path -> {rule -> set(dates)}}
    path_order: ordered list of paths seen in current window
    curr_window / prev_window: number of days in each window (denominator)
    """
    details = []
    section_pass_days = 0
    section_passes = 0
    section_fails = 0
    n_paths = len(path_order)

    for path in path_order:
        rule_days = curr_firing.get(path, {})
        rules = sorted(rule_days.keys())

        # Any-rule pass days for this path (used for section-level scoring)
        any_rule_days = set()
        for rule in rules:
            any_rule_days |= rule_days[rule]
        path_pass_days = len(any_rule_days)
        section_pass_days += path_pass_days
        path_rate = path_pass_days / curr_window if curr_window else 0

        if path_rate == 1.0:
            section_passes += 1
        elif path_rate == 0.0:
            section_fails += 1

        if not rules:
            # Path never passed in current window — one FAIL row, no rule
            prev_rate = None
            if prev_firing is not None and prev_window:
                prev_any = set()
                for rd in prev_firing.get(path, {}).values():
                    prev_any |= rd
                prev_rate = len(prev_any) / prev_window
            trend, prev_score = get_trend(0.0, prev_rate)
            row = {'path': path, 'score': 'Fail'}
            if trend:
                row['trend'] = trend
                row['prev'] = prev_score
            details.append(row)
        else:
            # One row per rule that fired at least once in the current window
            for rule in rules:
                days_fired = len(rule_days[rule])
                curr_rate = days_fired / curr_window if curr_window else 0
                prev_rate = None
                if prev_firing is not None and prev_window:
                    prev_days = len(prev_firing.get(path, {}).get(rule, set()))
                    prev_rate = prev_days / prev_window
                trend, prev_score = get_trend(curr_rate, prev_rate)
                row = {'path': path, 'rule': rule, 'score': fmt_score(curr_rate)}
                if trend:
                    row['trend'] = trend
                    row['prev'] = prev_score
                details.append(row)

    section_rate = section_pass_days / (curr_window * n_paths) if curr_window and n_paths else 0
    return {
        'section': sec_info['name'],
        'url': sec_info['url'],
        'details': details,
        'tests': n_paths,
        'passes': section_passes,
        'fails': section_fails,
        'score': fmt_pct(section_rate),
    }


def main():
    args = parse_args()
    compare_days = args.compare_days if args.compare_days is not None else args.days

    # Current window ends yesterday by default; previous window sits immediately before it
    curr_end = date.fromisoformat(args.end_date) if args.end_date else date.today() - timedelta(days=1)
    curr_start = curr_end - timedelta(days=args.days - 1)
    prev_end = curr_start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=compare_days - 1)

    print(f'Current window:  {curr_start} – {curr_end} ({args.days} days requested)')

    curr_records, curr_window = load_records(args.data_dir, curr_start, args.days)
    sections, curr_firing, path_order = index_records(curr_records)

    prev_firing_by_section = None
    prev_window = 0
    if compare_days:
        prev_records, prev_window = load_records(args.data_dir, prev_start, compare_days)
        _, prev_firing_raw, _ = index_records(prev_records)
        prev_firing_by_section = prev_firing_raw

    print(f'Current window:  {curr_window} days with data')
    if compare_days:
        print(f'Previous window: {prev_window} days with data')

    os.makedirs(args.output_dir, exist_ok=True)
    for key, sec_info in sections.items():
        prev_firing = prev_firing_by_section.get(key) if prev_firing_by_section else None
        data = build_section_yaml(
            sec_info,
            curr_firing[key],
            prev_firing,
            list(path_order[key].keys()),
            curr_window,
            prev_window,
        )
        out_path = os.path.join(args.output_dir, f'{key}.yml')
        with open(out_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        print(f'  Written {out_path}')


if __name__ == '__main__':
    main()
