# Usage

1. Clone the repo.
1. Change directory into the repo.
1. Pull the docker image if you want/need to update: `docker pull ghcr.io/zaproxy/zaproxy:nightly`
1. Run the tests: `docker run --rm -v $(pwd):/zap/wrk/:rw -t zaproxy/zap-nightly /zap/wrk/scans/auth/auth_plan_tests.sh`

---

1. To run a one-off: `zaproxy -cmd -autorun $PWD/scans/auth/plans_and_scripts/testfire/csa.yaml`. (Where `testfire` [the parent of the plans], is the "target".)

> [!NOTE]
> If you're using envvars to pass values into plan execution make sure you're accessing ZAP directly and not through other scripts/shells. For example on Kali, use: `/usr/share/zaproxy/zap.sh cmd -autorun $PWD/scans/auth/plans_and_scripts/testfire/bba.yaml`
> If you're trying to execute a BBA plan locally you will need to source the associated variables file first, ex: `source $PWD/scans/auth/plans_and_scripts/testfire/vars`

## Types

- bba - Browser Based Auth
- bbaplus - Browser Based Auth with manual config or extra steps
- csa - Client Script Auth
