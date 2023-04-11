#!/bin/bash

#Installing python3 & pip
apt-get install python3 -y
apt-get install pip -y
# Installing required Python3 modules
pip3 install urllib3
pip3 install beautifulsoup4
pip3 install requests
pip3 install colorama
# Installing prerequisites
sudo apt-get update
sudo apt-get -y install curl git
# Installing Golang
sudo apt-get -y install golang
go install github.com/tomnomnom/gf@latest
# Making gf as evniroimental variable
cp ~/go/bin/gf /usr/bin/
# Creating root directory for gf modules
mkdir ~/.gf
# Installing gf modules
git clone https://github.com/Sherlock297/gf_patterns.git
# Moving modules to root gf directory
cd gf_patterns/
cp *.json ~/.gf
gf -list
# Deleting unwanted files
cd ../
rm -r gf_patterns
