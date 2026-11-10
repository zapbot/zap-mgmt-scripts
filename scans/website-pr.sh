#!/bin/bash
# Pushes scan results in a zaproxy-website clone to the bot's fork and raises a PR if they changed.
#
# Usage: website-pr.sh <website-clone-dir> <data-dir> <branch> <commit-message>
#   website-pr.sh zaproxy-website site/data/scans/benchmark owasp-benchmark "Updated OWASP Benchmark Results"
#
# Expects the clone to have an 'upstream' remote (zaproxy/zaproxy-website) and an 'origin' remote
# (the bot's fork), and ZAPBOT_TOKEN to be set in the environment.
# The branch is always reset to the latest upstream and pushed, even if the results have not changed.
# A PR is only raised if they have.

set -euo pipefail

if [ $# -ne 4 ]; then
  echo "Usage: $0 <website-clone-dir> <data-dir> <branch> <commit-message>" >&2
  exit 1
fi

WEBSITE_DIR=$1
DATA_DIR=$2
BRANCH=$3
MESSAGE=$4

cd "$WEBSITE_DIR"

# Always base the branch on the latest upstream, whatever it held before
git checkout -B "$BRANCH" upstream/HEAD

# Stage first so that new (untracked) result files count as changes
git add "$DATA_DIR"
if git diff --cached --quiet; then
  CHANGES=false
else
  CHANGES=true
  git commit -sm "$MESSAGE"
fi

git push -u origin "$BRANCH" -f

if [ "$CHANGES" = true ]; then
  echo "$ZAPBOT_TOKEN" | gh auth login --with-token
  gh repo set-default zaproxy/zaproxy-website
  gh pr create --fill || true
else
  echo "No changes to $DATA_DIR, branch $BRANCH updated but no PR raised"
fi
