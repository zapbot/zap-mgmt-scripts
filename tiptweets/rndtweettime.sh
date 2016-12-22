#!/bin/bash
script="/usr/bin/python rndtweet.py"
min=$(( 24 * 60 ))
rmin=$(( $RANDOM % $min ))
at -f "$script" now+${rmin}min