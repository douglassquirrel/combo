## Installation on heroku

1. Sign up for a [Heroku account](https://www.heroku.com).
2. Add the [Bigwig addon](https://addons.heroku.com/rabbitmq-bigwig).
2. Install the [Heroku toolbelt](https://toolbelt.heroku.com) locally.
3. Pick an app name (HEROKU_APP in the below).
4. Clone the combo repository (local path to this clone is LOCAL_REPO below).
5. Run these commands:

        heroku apps:create HEROKU_APP
        cd LOCAL_REPO
        git remote add heroku git@heroku.com:HEROKU_APP.git
        git push heroku master
        heroku ps:scale web=1
        heroku ps:scale archivist=1
        heroku open

## Installation on fresh install of Ubuntu Linux 14.04 and Postgres

AWS: set up RDS Postgres instance and EC2 Ubuntu instance

Postgres:

Create user called combo
    createuser combo
Create database called combo
    createdb combo
Create facts table in combo
    psql combo
    Paste "CREATE TABLE facts (
        id serial primary key,
        topic character varying(255),
        ts timestamp without time zone,
        content json
    );"
Give combo user access to facts table
    "GRANT ALL PRIVILEGES ON facts TO combo;" (at the psql prompt)

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

## Installation on OS X

This is intended for local development, not a production server

Install Homebrew (if you somehow haven't)
    Read http://brew.sh/ for details
Install Postgres
    brew install postgresql
Start Postgres
    postgres -D /usr/local/var/postgres &
Install RabbitMQ
    brew install rabbitmq
Start RabbitMQ
    /usr/local/opt/rabbitmq/sbin/rabbitmq-server &

Then follow the instructions above to setup Postgres