#!/bin/bash

for d in ./scans/auth/plans_and_scripts/**/; do
  echo $d
  if ! [[ -s "$d/vars.env" ]];
  then
    # Here we'd get values from the secrets store
    echo Secret
  else
    cat "$d"/vars.env | tee -a ./scans/auth/all_vars.env > /dev/null
  fi
done
