Installation on fresh install of Ubuntu Linux 14.04 and Postgres

AWS: set up RDS Postgres instance and EC2 Ubuntu instance

On EC2 instance:
    sudo apt-get update
    sudo apt-get install git
    git clone https://github.com/douglassquirrel/combo.git
    cd combo/install
    ./install.sh
    ./test-rabbit.py localhost
    ./test-postgres.py [postgres host]

Then from remote machine

    ./test-rabbit.py [host]
    ./test-postgres.py [postgres host]

    