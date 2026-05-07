#!/usr/bin/env python3
"""Compare ZAP AJAX spider and Client spider across one or more target sites.

Usage:
    compare_spiders.py --zap /path/to/zap --site https://example.com/
    compare_spiders.py --zap /path/to/zap --sites std-sites.txt

Requires: pyyaml (pip install pyyaml)
"""

import argparse
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import yaml

# PyYAML treats bare '=' as the YAML 1.1 value type, which SafeLoader has no
# constructor for. ZAP exports can produce this in POST data fields.
yaml.SafeLoader.add_constructor(
    "tag:yaml.org,2002:value",
    lambda loader, node: loader.construct_scalar(node),
)

HEADERS = ["Site", "Atime", "Ctime", "StCom", "StAo", "StCo", "CmCom", "CmAo", "CmCo"]
KEYS    = ["site", "atime", "ctime", "st_com", "st_ao", "st_co", "cm_com", "cm_ao", "cm_co"]


def parse_args():
    p = argparse.ArgumentParser(
        description="Compare ZAP AJAX spider vs Client spider across target sites"
    )
    sites_group = p.add_mutually_exclusive_group(required=True)
    sites_group.add_argument("--site", metavar="URL", help="Single target URL")
    sites_group.add_argument(
        "--sites", metavar="FILE", help="File with target URLs, one per line"
    )
    p.add_argument(
        "--zap",
        metavar="DIR",
        default=os.environ.get("ZAP_DIR"),
        help="ZAP installation directory containing zap.sh (or set ZAP_DIR env var)",
    )
    p.add_argument("--port", type=int, default=9090, help="ZAP port (default: 9090)")
    p.add_argument(
        "--out",
        metavar="DIR",
        default="results",
        help="Root output directory for scan results (default: results)",
    )
    return p.parse_args()


def load_sites(args):
    if args.site:
        return [args.site.strip()]
    with open(args.sites) as f:
        return [
            line.strip()
            for line in f
            if line.strip() and not line.startswith("#")
        ]


def url_to_dirname(url):
    """Convert a URL to a safe filesystem directory name."""
    return (
        url.replace("://", "_")
           .replace("/", "_")
           .replace(".", "-")
           .strip("_")
    )


def make_run_config(template_path, output_dir):
    """
    Write a temp YAML config derived from template_path with each export
    job's fileName replaced by an absolute path under output_dir.
    Returns the temp file path; caller must delete it.
    """
    with open(template_path) as f:
        config = yaml.safe_load(f)

    for job in config.get("jobs", []):
        if job.get("type") == "export":
            fname = job["parameters"]["fileName"]
            job["parameters"]["fileName"] = str(output_dir / fname)

    fd, tmp_path = tempfile.mkstemp(suffix=".yaml", prefix="zap_run_")
    with os.fdopen(fd, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    return Path(tmp_path)


def run_zap(zap_sh, port, autorun_yaml, target, data_dir):
    """Run ZAP in cmd mode against target. Returns elapsed seconds."""
    data_dir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["target"] = target
    cmd = [
        str(zap_sh),
        "-cmd",
        "-port", str(port),
        "-autorun", str(autorun_yaml),
        "-dir", str(data_dir),
    ]
    t0 = time.monotonic()
    result = subprocess.run(cmd, env=env)
    elapsed = time.monotonic() - t0
    if result.returncode != 0:
        print(f"  WARNING: ZAP exited with code {result.returncode}", file=sys.stderr)
    return elapsed


def extract_nodes(data, prefix=""):
    """Recursively collect all hierarchical node paths from a ZAP YAML export."""
    nodes = set()
    if isinstance(data, list):
        for item in data:
            nodes.update(extract_nodes(item, prefix))
    elif isinstance(data, dict) and "node" in data:
        path = f"{prefix}/{data['node']}" if prefix else str(data["node"])
        nodes.add(path)
        for child in data.get("children") or []:
            nodes.update(extract_nodes(child, path))
    return nodes


def load_nodes(path):
    """Load the node set from a ZAP YAML export. Returns empty set if missing."""
    if not path.exists():
        return set()
    with open(path) as f:
        data = yaml.safe_load(f)
    return extract_nodes(data) if data else set()


def compare_exports(ajax_path, client_path):
    """Return (common, ajax_only, client_only) node counts for two exports."""
    ajax_nodes   = load_nodes(ajax_path)
    client_nodes = load_nodes(client_path)
    return (
        len(ajax_nodes & client_nodes),
        len(ajax_nodes - client_nodes),
        len(client_nodes - ajax_nodes),
    )


def fmt_time(seconds):
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}"


def compute_col_widths(results):
    """Compute column widths wide enough for headers and all data values."""
    widths = []
    for header, key in zip(HEADERS, KEYS):
        vals = [str(r[key]) for r in results]
        widths.append(max(len(header), max(len(v) for v in vals)) + 2)
    return widths


def format_cell(value, width, align):
    """Return a table cell string of exactly `width` chars with 1-space padding."""
    inner = width - 2
    s = str(value)
    if align == "left":
        return f" {s:<{inner}} "
    elif align == "right":
        return f" {s:>{inner}} "
    else:
        return f" {s:^{inner}} "


def build_summary_row(results):
    """Average the time columns and total the count columns across results."""
    n = len(results)
    return {
        "site":   "Summary",
        "atime":  fmt_time(sum(r["atime"] for r in results) / n),
        "ctime":  fmt_time(sum(r["ctime"] for r in results) / n),
        "st_com": sum(r["st_com"] for r in results),
        "st_ao":  sum(r["st_ao"]  for r in results),
        "st_co":  sum(r["st_co"]  for r in results),
        "cm_com": sum(r["cm_com"] for r in results),
        "cm_ao":  sum(r["cm_ao"]  for r in results),
        "cm_co":  sum(r["cm_co"]  for r in results),
    }


def print_table(results):
    if not results:
        return

    display_rows = [
        {**r, "atime": fmt_time(r["atime"]), "ctime": fmt_time(r["ctime"])}
        for r in results
    ]
    summary = build_summary_row(results)
    all_rows = display_rows + [summary]

    widths = compute_col_widths(all_rows)

    header_aligns = ["left"] + ["center"] * (len(HEADERS) - 1)
    header_cells  = [
        format_cell(h, w, a) for h, w, a in zip(HEADERS, widths, header_aligns)
    ]
    sep = "+" + "+".join("-" * w for w in widths) + "+"

    print("|" + "|".join(header_cells) + "|")
    print(sep)

    data_aligns = ["left"] + ["right"] * (len(KEYS) - 1)
    for r in display_rows:
        cells = [
            format_cell(r[k], w, a)
            for k, w, a in zip(KEYS, widths, data_aligns)
        ]
        print("|" + "|".join(cells) + "|")

    print(sep)
    summary_cells = [
        format_cell(summary[k], w, a)
        for k, w, a in zip(KEYS, widths, data_aligns)
    ]
    print("|" + "|".join(summary_cells) + "|")


def main():
    args = parse_args()

    if not args.zap:
        sys.exit("ERROR: specify --zap DIR or set ZAP_DIR environment variable")

    zap_sh = Path(args.zap) / "zap.sh"
    if not zap_sh.exists():
        sys.exit(f"ERROR: zap.sh not found at {zap_sh}")

    script_dir  = Path(__file__).parent.resolve()
    ajax_tmpl   = script_dir / "ajax.yaml"
    client_tmpl = script_dir / "client.yaml"

    for f, name in [(ajax_tmpl, "ajax.yaml"), (client_tmpl, "client.yaml")]:
        if not f.exists():
            sys.exit(f"ERROR: {name} not found at {f}")

    sites   = load_sites(args)
    out_dir = Path(args.out).resolve()
    results = []

    for site in sites:
        print(f"\nProcessing: {site}")
        site_dir    = out_dir / url_to_dirname(site)
        site_dir.mkdir(parents=True, exist_ok=True)

        print("  Running AJAX spider ...")
        ajax_cfg = make_run_config(ajax_tmpl, site_dir)
        try:
            atime = run_zap(zap_sh, args.port, ajax_cfg, site, site_dir / "ajax-data")
        finally:
            ajax_cfg.unlink(missing_ok=True)
        print(f"  Done in {fmt_time(atime)}")

        print("  Running Client spider ...")
        client_cfg = make_run_config(client_tmpl, site_dir)
        try:
            ctime = run_zap(zap_sh, args.port, client_cfg, site, site_dir / "client-data")
        finally:
            client_cfg.unlink(missing_ok=True)
        print(f"  Done in {fmt_time(ctime)}")

        st_com, st_ao, st_co = compare_exports(
            site_dir / "ajax-site.yaml", site_dir / "client-site.yaml"
        )
        cm_com, cm_ao, cm_co = compare_exports(
            site_dir / "ajax-map.yaml", site_dir / "client-map.yaml"
        )

        results.append({
            "site":   site,
            "atime":  atime,
            "ctime":  ctime,
            "st_com": st_com,
            "st_ao":  st_ao,
            "st_co":  st_co,
            "cm_com": cm_com,
            "cm_ao":  cm_ao,
            "cm_co":  cm_co,
        })

    print()
    print_table(results)


if __name__ == "__main__":
    main()
