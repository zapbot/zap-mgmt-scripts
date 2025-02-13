# Usage

1. Clone the repo.
1. Change directory into the repo.
1. Pull the docker image if you want/need to update: `docker pull ghcr.io/zaproxy/zaproxy:nightly`
1. Run the tests: `docker run --rm -v $(pwd):/zap/wrk/:rw -t zaproxy/zap-nightly /zap/wrk/scans/auth/auth_plan_tests.sh`

---

1. To run a one-off: `zaproxy -cmd -autorun $PWD/scans/auth/plans_and_scripts/testfire/csa.yaml`. (Where `testfire` [the parent of the plans], is the "target".)

## Types

- bba - Browser Based Auth
- bbaplus - Browser Based Auth with manual config or extra steps
- csa - Client Script Auth
