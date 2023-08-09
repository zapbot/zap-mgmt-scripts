# ZAP Management Scripts
This repo contains scripts for ZAP automation.

The information maintained by this repo see the [ZAPbot Homepage](http://zapbot.github.io/zap-mgmt-scripts/index.html)

## ZAP Automated Tests
The following instructions have been used to set up an AWS instance for running the ZAP automated tests - they will need tweaking for other environments.

The current instance being used is a t2.medium running with Ubuntu trusty and 24Gb disk.

From a bare bones install, as root run:
* apt-get update -y
* apt-get -y install python-pip
* pip install zaproxy
* pip install awscli
* curl -sSL https://get.docker.com/ | sh
* usermod -aG docker ubuntu

As the user that will run the tests (default ubuntu) run:
* git clone https://github.com/zapbot/zap-mgmt-scripts.git
* git clone -b gh-pages --single-branch https://github.com/zapbot/zap-mgmt-scripts.git zap-mgmt-scripts_gh-pages

In order to commit to the zapbot repo and to get aws sns messages the following files are also needed, for obvious reasons their contents arent given here ;)
* .awssns
* .gitconfig
* .netrc


