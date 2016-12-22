#!/bin/bash
script="tiptweets/rndtweettime.sh"
min=$(( 24 * 60 ))
rmin=$(( $RANDOM % $min ))
at -f "$script" now+${rmin}min
