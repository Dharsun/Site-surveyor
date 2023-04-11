#!/bin/bash

#!/bin/bash

apt-get install python3
apt-get install pip

# Install required Python3 modules
pip3 install urllib3
pip3 install beautifulsoup4
pip3 install requests
pip3 install colorama



# Install prerequisites
sudo apt-get update
sudo apt-get -y install curl git

# Install Golang
sudo apt-get -y install golang

go install github.com/tomnomnom/gf@latest

cp ~/go/bin/gf /usr/bin/

mkdir ~/.gf

git clone https://github.com/Sherlock297/gf_patterns.git

cd gf_patterns/

cp *.json ~/.gf

gf -list


