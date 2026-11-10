#!/bin/bash
# Prints scan results to the job log: the full file in a collapsed group, then the summary lines.
# Useful for debugging, and for when the website PR cannot be raised.
#
# Usage: show-results.sh <results-file> [title]

set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <results-file> [title]" >&2
  exit 1
fi

FILE=$1
TITLE=${2:-$(basename "$FILE" .yml)}

echo "::group::Full results for $TITLE"
cat "$FILE"
echo "::endgroup::"
echo "===== $TITLE summary ====="
grep -E '^(section|tests|passes|fails|score):' "$FILE" || true
