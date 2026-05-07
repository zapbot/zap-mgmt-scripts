# Spider Comparison Script

A script for comparing ZAP's two modern spiders — the **AJAX spider** and the **Client spider** — across one or more target sites.

## Overview

`compare_spiders.py` runs both spiders against each target, exports the Site Tree and Client Map from each run, then prints a side-by-side comparison table showing how many nodes each spider found, how many were unique to each, and how long each run took.

## Requirements

- Python 3
- [PyYAML](https://pypi.org/project/PyYAML/): `pip install pyyaml`
- A ZAP installation directory containing `zap.sh`

## Usage

```bash
# Single site
python3 compare_spiders.py --zap /path/to/zap --site https://example.com/

# Multiple sites from a file
python3 compare_spiders.py --zap /path/to/zap --sites std-sites.txt

# Set ZAP path via environment variable instead
export ZAP_DIR=/path/to/zap
python3 compare_spiders.py --sites std-sites.txt

# Custom output directory and port
python3 compare_spiders.py --zap /path/to/zap --sites std-sites.txt --out my-results --port 8090
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--site URL` | — | Single target URL (mutually exclusive with `--sites`) |
| `--sites FILE` | — | File containing target URLs, one per line (lines starting with `#` are ignored) |
| `--zap DIR` | `$ZAP_DIR` | ZAP installation directory (must contain `zap.sh`) |
| `--port PORT` | `9090` | Port ZAP listens on |
| `--out DIR` | `results` | Root directory for scan output files |

## Output

Results are printed as a table after all sites have been scanned:

```
| Site                              | Atime | Ctime | StCom | StAo | StCo | CmCom | CmAo | CmCo |
+-----------------------------------+-------+-------+-------+------+------+-------+------+------+
| https://brokencrystals.com/       |  2:24 |  1:39 |   103 |    2 |    3 |   104 |    8 |   12 |
| https://ginandjuice.shop/         |  0:59 |  0:36 |    92 |    0 |   20 |   109 |    0 |   31 |
| https://juice-shop.herokuapp.com/ | 10:02 | 12:23 |   603 |   10 |    0 |   500 |    6 |    0 |
```

### Column definitions

| Column | Description |
|--------|-------------|
| `Atime` | Time taken by the AJAX spider (mm:ss) |
| `Ctime` | Time taken by the Client spider (mm:ss) |
| `StCom` | Site Tree nodes found by **both** spiders |
| `StAo` | Site Tree nodes found by the **AJAX spider only** |
| `StCo` | Site Tree nodes found by the **Client spider only** |
| `CmCom` | Client Map nodes found by **both** spiders |
| `CmAo` | Client Map nodes found by the **AJAX spider only** |
| `CmCo` | Client Map nodes found by the **Client spider only** |

## Output files

For each site scanned, the following files are written under `--out`:

```
results/
  {site}/
    ajax-site.yaml      ← Site Tree export from the AJAX spider run
    ajax-map.yaml       ← Client Map export from the AJAX spider run
    client-site.yaml    ← Site Tree export from the Client spider run
    client-map.yaml     ← Client Map export from the Client spider run
    ajax-data/          ← ZAP home directory for the AJAX spider run
    client-data/        ← ZAP home directory for the Client spider run
```

## Configuration

The spiders are configured by `ajax.yaml` and `client.yaml` in this directory. Both run 6 browser instances with a 5-minute maximum duration. Edit these files to adjust spider parameters such as `numberOfBrowsers` or `maxDuration`.

## Sites file format

`std-sites.txt` contains a set of public test targets. Lines beginning with `#` are treated as comments:

```
# Public test sites
https://brokencrystals.com/
https://ginandjuice.shop/
https://juice-shop.herokuapp.com/
https://public-firing-range.appspot.com/
https://security-crawl-maze.app/
```
