# Usage

1. Clone the repo.
1. Change directory into the repo.
1. Pull the docker image if you want/need to update: `docker pull ghcr.io/zaproxy/zaproxy:nightly`
1. Create `scans/auth/all_vars.env` with standard `key=value` pairs. Keys should be `<target><user_or_pass>=value`, ex: `foo_user=jsmith`, `foo_pass=demo1234` (assuming a target known as `foo`).
1. Run the tests: `docker run --rm -v $(pwd):/zap/wrk/:rw --env-file scans/auth/all_vars.env -t zaproxy/zap-nightly /zap/wrk/scans/auth/auth_plan_tests.sh`


## Types

- bba - Browser Based Auth
- bbaplus - Browser Based Auth with manual config or extra steps
- csa - Client Script Auth

> [!IMPORTANT]
> If `output.yml` does not contain a result for a given Type, then that type is unnecessary because easier options exist. Ex: If BBA works there likely won't be a bbaplus/csa plan nor result.

# One-offs

1. To run a one-off: `docker run --rm -v $(pwd):/zap/wrk/:rw --env-file scans/auth/all_vars.env -t zaproxy/zap-nightly /zap/zap.sh -cmd -autorun /zap/wrk/scans/auth/plans_and_scripts/testfire/bba.yaml`.
