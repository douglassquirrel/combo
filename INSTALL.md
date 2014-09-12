Installation on fresh install of Ubuntu Linux 14.04
Tested on AWS micro instance - open all ports in firewall

    sudo apt-get update
    sudo apt-get install git
    git clone https://github.com/douglassquirrel/combo.git
    cd combo/install
    ./install.sh
    ./test-rabbit.py localhost

Then from remote machine

    ./test-rabbit.py [host]

    