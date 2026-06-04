#!/usr/bin/env python3
"""
Run ZAP vs Firing Range tests locally.

Configuration is read from run-firingrange.properties in the same directory.
Command-line arguments override property file settings.

Run with --help for usage information.
"""

import argparse
import configparser
import os
import shutil
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
PROPERTIES_FILE = os.path.join(SCRIPT_DIR, "run-firingrange.properties")

DEFAULT_DOCKER_IMAGE = "ghcr.io/zaproxy/zaproxy:nightly"
DEFAULT_DEV_BUILD_DIR = os.path.join(os.path.dirname(REPO_DIR), "zaproxy")
DEFAULT_OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")

ALL_SECTIONS = [
    "address",
    "angular",
    "clickjacking",
    "dom",
    "escape",
    "leakedcookie",
    "mixedcontent",
    "reflected",
    "remoteinclude",
    "reverseclickjacking",
    "urldom"
]


def load_properties():
    props = {
        "output_dir": DEFAULT_OUTPUT_DIR,
        "docker_image": DEFAULT_DOCKER_IMAGE,
        "use_dev_build": "false",
        "dev_build_dir": DEFAULT_DEV_BUILD_DIR,
        "sections": "all",
    }
    if not os.path.exists(PROPERTIES_FILE):
        return props
    config = configparser.ConfigParser()
    with open(PROPERTIES_FILE) as f:
        config.read_string("[DEFAULT]\n" + f.read())
    for key in props:
        if key in config["DEFAULT"]:
            props[key] = config["DEFAULT"][key]
    return props


def resolve_path(path, base):
    if os.path.isabs(path):
        return path
    return os.path.normpath(os.path.join(base, path))


def create_scoring_script(section, dir_override=None):
    """Concatenate fr-<section>.js + firing-range-score-main.js into firing-range-score.js.

    dir_override replaces the /zap/wrk/ DIR variable for native (non-Docker) runs.
    """
    section_js = os.path.join(SCRIPT_DIR, f"fr-{section}.js")
    main_js = os.path.join(SCRIPT_DIR, "firing-range-score-main.js")
    output_js = os.path.join(SCRIPT_DIR, "firing-range-score.js")

    with open(section_js) as f:
        section_content = f.read()

    if dir_override is not None:
        section_content = section_content.replace(
            'var DIR = "/zap/wrk/"',
            f'var DIR = "{dir_override}/";',
        )

    with open(main_js) as f:
        main_content = f.read()

    with open(output_js, "w") as out:
        out.write(section_content)
        out.write(main_content)


def create_local_yaml(section, local_dir):
    """Write a copy of fr-<section>.yaml with /zap/wrk/ replaced by local_dir."""
    yaml_src = os.path.join(SCRIPT_DIR, f"fr-{section}.yaml")
    yaml_dst = os.path.join(SCRIPT_DIR, f"fr-{section}-local.yaml")

    with open(yaml_src) as f:
        content = f.read()

    content = content.replace("/zap/wrk/", local_dir + "/")

    with open(yaml_dst, "w") as f:
        f.write(content)

    return yaml_dst


def touch_output_yml(section):
    path = os.path.join(SCRIPT_DIR, f"{section}.yml")
    open(path, "w").close()
    os.chmod(path, 0o666)
    return path


def copy_result(section_yml, section, output_dir):
    if os.path.getsize(section_yml) > 0:
        os.makedirs(output_dir, exist_ok=True)
        dest = os.path.join(output_dir, f"{section}.yml")
        shutil.copy(section_yml, dest)
        print(f"  Results saved: {dest}")
        return True
    print(f"  WARNING: no output produced for section '{section}'")
    return False


def run_docker(section, docker_image, output_dir):
    print(f"\n{'='*60}")
    print(f"Section: {section}  |  Docker: {docker_image}")
    print("=" * 60)

    create_scoring_script(section)
    output_yml = touch_output_yml(section)

    cmd = [
        "docker", "run",
        "-v", f"{SCRIPT_DIR}:/zap/wrk/:rw",
        "-t", docker_image,
        "zap.sh", "-cmd", "-silent", "-autorun", f"/zap/wrk/fr-{section}.yaml",
    ]
    print(f"$ {' '.join(cmd)}\n")
    result = subprocess.run(cmd)

    copy_result(output_yml, section, output_dir)
    return result.returncode


def run_dev_build(section, dev_build_dir, output_dir):
    print(f"\n{'='*60}")
    print(f"Section: {section}  |  Dev build: {dev_build_dir}")
    print("=" * 60)

    if not os.path.isdir(dev_build_dir):
        print(f"ERROR: dev build directory not found: {dev_build_dir}")
        return 1

    gradlew = os.path.join(dev_build_dir, "gradlew")
    if not os.path.isfile(gradlew):
        print(f"ERROR: gradlew not found: {gradlew}")
        return 1

    # Create scoring script with DIR pointing to SCRIPT_DIR so output lands there.
    create_scoring_script(section, dir_override=SCRIPT_DIR)

    local_yaml = create_local_yaml(section, SCRIPT_DIR)
    output_yml = touch_output_yml(section)

    try:
        cmd = [gradlew, ":zap:run", f"--args=-cmd -silent -autorun {local_yaml}"]
        print(f"$ {' '.join(cmd)}\n")
        result = subprocess.run(cmd, cwd=dev_build_dir)
    finally:
        if os.path.exists(local_yaml):
            os.remove(local_yaml)

    copy_result(output_yml, section, output_dir)
    return result.returncode


def parse_sections(sections_str):
    if sections_str.strip().lower() == "all":
        return list(ALL_SECTIONS)
    sections = [s.strip() for s in sections_str.split(",")]
    unknown = [s for s in sections if s not in ALL_SECTIONS]
    if unknown:
        print(f"ERROR: unknown section(s): {', '.join(unknown)}")
        print(f"Available: {', '.join(ALL_SECTIONS)}")
        sys.exit(1)
    return sections


def main():
    props = load_properties()

    parser = argparse.ArgumentParser(
        description="Run ZAP vs Firing Range tests locally.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Available sections:\n  " + "\n  ".join(ALL_SECTIONS) + "\n\n"
            "Settings can be persisted in run-firingrange.properties."
        ),
    )
    parser.add_argument(
        "--sections", "-s",
        metavar="LIST",
        help="Comma-separated sections to run, or 'all' (default: all)",
    )
    parser.add_argument(
        "--output-dir", "-o",
        metavar="DIR",
        help=f"Output directory for results (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--docker-image",
        metavar="IMAGE",
        help=f"Docker image to use (default: {DEFAULT_DOCKER_IMAGE})",
    )
    parser.add_argument(
        "--dev-build",
        action="store_true",
        default=None,
        help="Use a local ZAP dev build instead of Docker",
    )
    parser.add_argument(
        "--dev-build-dir",
        metavar="DIR",
        help=f"Path to the zaproxy repo root (default: {DEFAULT_DEV_BUILD_DIR})",
    )

    args = parser.parse_args()

    output_dir = resolve_path(
        args.output_dir or props["output_dir"],
        base=SCRIPT_DIR,
    )
    docker_image = args.docker_image or props["docker_image"]
    use_dev_build = (
        args.dev_build
        if args.dev_build is not None
        else props.get("use_dev_build", "false").lower() in ("true", "yes", "1")
    )
    dev_build_dir = resolve_path(
        args.dev_build_dir or props["dev_build_dir"],
        base=REPO_DIR,
    )
    sections = parse_sections(args.sections or props.get("sections", "all"))

    print("ZAP vs Firing Range — Local Runner")
    print(f"Sections : {', '.join(sections)}")
    print(f"Output   : {output_dir}")
    if use_dev_build:
        print(f"Mode     : dev build ({dev_build_dir})")
    else:
        print(f"Mode     : Docker ({docker_image})")

    failures = []
    for section in sections:
        if use_dev_build:
            rc = run_dev_build(section, dev_build_dir, output_dir)
        else:
            rc = run_docker(section, docker_image, output_dir)
        if rc != 0:
            failures.append(section)

    print(f"\n{'='*60}")
    if failures:
        print(f"FAILED sections: {', '.join(failures)}")
        sys.exit(1)
    else:
        print(f"All {len(sections)} section(s) completed.")
        print(f"Results in: {output_dir}")


if __name__ == "__main__":
    main()
