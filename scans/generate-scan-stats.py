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
import urllib.request
from collections import defaultdict
from datetime import date, timedelta

import yaml

# Fixed columns for matrix-style website pages (crawlground / ssti).
# Always emit every column so never-passing tools/rules still show as Fail.
CRAWLGROUND_COLUMNS = ['standard', 'ajax', 'client']
SSTI_COLUMNS = [
    'rule_40012', 'rule_40026', 'rule_90025',
    'rule_90019', 'rule_90035', 'rule_90036',
]


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
    p.add_argument('--scan', default=None,
                   help='Scan name for Slack messages (default: basename of --data-dir)')
    p.add_argument('--slack-webhook', default=None,
                   help='Slack incoming webhook URL; if set, posts regressions (down trends)')
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

    A rule "firing" is not the same as a test "passing": for false-positive
    test cases, a fired rule means the scan incorrectly flagged the page, so
    the record's own `result` field (not rule presence) is the ground truth
    for pass/fail.

    Returns:
      sections:     {section_key -> {name, url}}
      firing:       {section_key -> {path -> {rule -> set(dates rule fired, any result)}}}
      pass_firing:  {section_key -> {path -> {rule -> set(dates rule fired with result==Pass)}}}
      path_pass:    {section_key -> {path -> set(dates with result==Pass)}}
      paths:        {section_key -> ordered list of paths (insertion order)}
    """
    sections = {}
    firing = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))
    pass_firing = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))
    path_pass = defaultdict(lambda: defaultdict(set))
    path_order = defaultdict(dict)  # section_key -> {path: None} (ordered set)

    for r in records:
        key = r.get('section_key')
        if not key or r.get('result') == 'Broken':
            continue
        if key not in sections:
            sections[key] = {'name': r.get('section', key), 'url': r.get('url', '')}
        path = r['path']
        path_order[key][path] = None
        is_pass = r.get('result') == 'Pass'
        if is_pass:
            path_pass[key][path].add(r['date'])
        for rule in r.get('rules', []):
            firing[key][path][rule].add(r['date'])
            if is_pass:
                pass_firing[key][path][rule].add(r['date'])

    return sections, firing, pass_firing, path_pass, path_order


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


def build_section_yaml(sec_info, curr_rules, curr_pass_firing, curr_path_pass,
                       prev_pass_firing, prev_path_pass, path_order,
                       curr_window, prev_window):
    """
    Build the YAML dict for one section and return a list of regressions.

    curr_rules:        {path -> {rule -> set(dates rule fired, any result)}} —
                       used only to know which rule rows to show.
    curr_pass_firing:  {path -> {rule -> set(dates rule fired with result==Pass)}}
    curr_path_pass:    {path -> set(dates with result==Pass)} — ground truth
                       for pass/fail (rule firing alone is not: for
                       false-positive test cases, firing means the scan
                       incorrectly flagged the page, i.e. a fail).
    path_order: ordered list of paths seen in current window
    curr_window / prev_window: number of days in each window (denominator)

    Returns (yaml_dict, regressions) where regressions is a list of
    {'path', optionally 'rule', 'prev', 'score'} dicts for down trends.
    """
    details = []
    regressions = []
    section_pass_days = 0
    section_passes = 0
    section_fails = 0
    n_paths = len(path_order)

    for path in path_order:
        rules = sorted(curr_rules.get(path, {}).keys())

        path_pass_days = len(curr_path_pass.get(path, set()))
        section_pass_days += path_pass_days
        path_rate = path_pass_days / curr_window if curr_window else 0

        if path_rate == 1.0:
            section_passes += 1
        elif path_rate == 0.0:
            section_fails += 1

        if not rules:
            # No rule ever fired for this path in the current window — one
            # row scored on the path's own pass rate (e.g. a false-positive
            # test case where correctly not firing means Pass).
            prev_rate = None
            if prev_path_pass is not None and prev_window:
                prev_rate = len(prev_path_pass.get(path, set())) / prev_window
            trend, prev_score = get_trend(path_rate, prev_rate)
            row = {'path': path, 'score': fmt_score(path_rate)}
            if trend:
                row['trend'] = trend
                row['prev'] = prev_score
                if trend == 'down':
                    regressions.append({'path': path, 'prev': prev_score,
                                        'score': fmt_score(path_rate)})
            details.append(row)
        else:
            # One row per rule that fired at least once in the current
            # window, scored on days that firing coincided with a Pass
            # result (so a false-positive-triggering rule scores as a fail).
            for rule in rules:
                pass_days = len(curr_pass_firing.get(path, {}).get(rule, set()))
                curr_rate = pass_days / curr_window if curr_window else 0
                prev_rate = None
                if prev_pass_firing is not None and prev_window:
                    prev_days = len(prev_pass_firing.get(path, {}).get(rule, set()))
                    prev_rate = prev_days / prev_window
                trend, prev_score = get_trend(curr_rate, prev_rate)
                row = {'path': path, 'rule': rule, 'score': fmt_score(curr_rate)}
                if trend:
                    row['trend'] = trend
                    row['prev'] = prev_score
                    if trend == 'down':
                        regressions.append({'path': path, 'rule': rule,
                                            'prev': prev_score, 'score': fmt_score(curr_rate)})
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
    }, regressions


def _column_rate(firing_for_path, column, window):
    """Pass rate for one matrix column over the window. Missing → 0."""
    if not window:
        return 0.0
    return len(firing_for_path.get(column, set())) / window


def _apply_column_score(row, column, curr_rate, prev_rate, path, regressions):
    """Set column score (+ optional trend) on row; record down trends."""
    score = fmt_score(curr_rate)
    row[column] = score
    trend, prev_score = get_trend(curr_rate, prev_rate)
    if trend:
        row[f'{column}_trend'] = trend
        row[f'{column}_prev'] = prev_score
        if trend == 'down':
            regressions.append({
                'path': path, 'rule': column,
                'prev': prev_score, 'score': score,
            })


def build_matrix_section_yaml(scan, sec_info, curr_firing, prev_firing,
                              path_order, curr_window, prev_window):
    """
    Build matrix-style YAML for crawlground or ssti.

    One row per path/title with a score (and optional trend) per fixed column.
    """
    if scan == 'crawlground':
        columns = CRAWLGROUND_COLUMNS
    elif scan == 'ssti':
        columns = SSTI_COLUMNS
    else:
        raise ValueError(f'Unknown matrix scan: {scan}')

    details = []
    regressions = []
    n_paths = len(path_order)
    col_full_passes = {c: 0 for c in columns}
    any_full_passes = 0

    for path in path_order:
        curr_path = curr_firing.get(path, {})
        prev_path = prev_firing.get(path, {}) if prev_firing is not None else {}

        if scan == 'crawlground':
            row = {'path': path, 'scheme': 'http'}
        else:
            row = {'title': path}

        any_curr_days = set()
        any_prev_days = set()

        for column in columns:
            curr_rate = _column_rate(curr_path, column, curr_window)
            prev_rate = None
            if prev_firing is not None and prev_window:
                prev_rate = _column_rate(prev_path, column, prev_window)
            _apply_column_score(row, column, curr_rate, prev_rate, path, regressions)
            if curr_rate == 1.0:
                col_full_passes[column] += 1
            any_curr_days |= curr_path.get(column, set())
            any_prev_days |= prev_path.get(column, set())

        if scan == 'ssti':
            any_curr = len(any_curr_days) / curr_window if curr_window else 0.0
            any_prev = None
            if prev_firing is not None and prev_window:
                any_prev = len(any_prev_days) / prev_window
            _apply_column_score(row, 'any', any_curr, any_prev, path, regressions)
            if any_curr == 1.0:
                any_full_passes += 1

        details.append(row)

    if scan == 'crawlground':
        # Overall score matches existing snapshot semantics (client spider).
        passes = col_full_passes['client']
        fails = n_paths - passes
        result = {
            'section': sec_info['name'],
            'target': sec_info['url'],
            'details': details,
            'tests': n_paths,
            'passes': passes,
            'standardPasses': col_full_passes['standard'],
            'ajaxPasses': col_full_passes['ajax'],
            'clientPasses': col_full_passes['client'],
            'fails': fails,
            'score': fmt_pct(passes / n_paths if n_paths else 0),
        }
    else:
        result = {
            'section': sec_info['name'],
            'details': details,
            'score': fmt_pct(any_full_passes / n_paths if n_paths else 0),
        }
        for column in columns:
            result[f'{column}_score'] = col_full_passes[column]
        result['any_score'] = any_full_passes

    return result, regressions


def post_slack_alert(scan, all_regressions, webhook_url):
    total = sum(len(r) for _, r in all_regressions)
    n_sections = len(all_regressions)
    lines = [f'⚠️ *ZAP scan regressions: {scan}* — {total} regression(s) across {n_sections} section(s)']
    # If there are many regressions the target is likely down — keep the message short
    if total <= 10:
        for section, regressions in all_regressions:
            lines.append(f'\n*{section}*')
            for r in regressions:
                rule = f' (rule {r["rule"]})' if 'rule' in r else ''
                lines.append(f'  • `{r["path"]}`{rule}: {r["prev"]} → {r["score"]}')
    else:
        lines.append('Large number of regressions — target site may be down or a scan rule has broken.')
    body = json.dumps({'text': '\n'.join(lines)}).encode()
    req = urllib.request.Request(webhook_url, data=body,
                                 headers={'Content-Type': 'application/json'})
    urllib.request.urlopen(req, timeout=10)


def main():
    args = parse_args()
    compare_days = args.compare_days if args.compare_days is not None else args.days
    scan = args.scan or os.path.basename(os.path.normpath(args.data_dir))

    # Current window ends yesterday by default; previous window sits immediately before it
    curr_end = date.fromisoformat(args.end_date) if args.end_date else date.today() - timedelta(days=1)
    curr_start = curr_end - timedelta(days=args.days - 1)
    prev_end = curr_start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=compare_days - 1)

    print(f'Current window:  {curr_start} – {curr_end} ({args.days} days requested)')

    curr_records, curr_window = load_records(args.data_dir, curr_start, args.days)
    sections, curr_firing, curr_pass_firing, curr_path_pass, path_order = index_records(curr_records)

    prev_firing_by_section = None
    prev_pass_firing_by_section = None
    prev_path_pass_by_section = None
    prev_window = 0
    if compare_days:
        prev_records, prev_window = load_records(args.data_dir, prev_start, compare_days)
        _, prev_firing_raw, prev_pass_firing_raw, prev_path_pass_raw, _ = index_records(prev_records)
        prev_firing_by_section = prev_firing_raw
        prev_pass_firing_by_section = prev_pass_firing_raw
        prev_path_pass_by_section = prev_path_pass_raw

    print(f'Current window:  {curr_window} days with data')
    if compare_days:
        print(f'Previous window: {prev_window} days with data')

    os.makedirs(args.output_dir, exist_ok=True)
    all_regressions = []
    for key, sec_info in sections.items():
        prev_firing = prev_firing_by_section.get(key) if prev_firing_by_section else None
        if scan in ('crawlground', 'ssti'):
            data, regressions = build_matrix_section_yaml(
                scan,
                sec_info,
                curr_firing[key],
                prev_firing,
                list(path_order[key].keys()),
                curr_window,
                prev_window,
            )
        else:
            prev_pass_firing = prev_pass_firing_by_section.get(key) if prev_pass_firing_by_section else None
            prev_path_pass = prev_path_pass_by_section.get(key) if prev_path_pass_by_section else None
            data, regressions = build_section_yaml(
                sec_info,
                curr_firing[key],
                curr_pass_firing[key],
                curr_path_pass[key],
                prev_pass_firing,
                prev_path_pass,
                list(path_order[key].keys()),
                curr_window,
                prev_window,
            )
        if regressions:
            all_regressions.append((sec_info['name'], regressions))
        out_path = os.path.join(args.output_dir, f'{key}.yml')
        with open(out_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        print(f'  Written {out_path}')

    if all_regressions:
        total = sum(len(r) for _, r in all_regressions)
        print(f'  {total} regression(s) detected across {len(all_regressions)} section(s)')
        if args.slack_webhook:
            post_slack_alert(scan, all_regressions, args.slack_webhook)
            print('  Slack alert posted')


if __name__ == '__main__':
    main()
