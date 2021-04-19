# Local files which handle specific stats
import docker
import github
import bitly
import groups

# Python imports
import os
import sys

def usage():
    print("stats.py collect | daily | website")

def collect():
    docker.collect()
    github.collect()
    bitly.collect()

def daily():
    docker.daily()
    github.daily()
    bitly.daily()

def website():
    docker.website()
    github.website()
    bitly.website()
    groups.website()

if __name__ == '__main__':
    if len(sys.argv) == 2:
        fn = sys.argv[1]
        if fn in globals():
            globals()[sys.argv[1]]()
        else:
            usage()
    else:
        usage()
