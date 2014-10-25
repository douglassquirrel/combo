## Installation on heroku

1. Sign up for a [Heroku account](https://www.heroku.com).
2. Install the [Heroku toolbelt](https://toolbelt.heroku.com).
2. Pick an app name (HEROKU_APP in the below).
3. Clone the combo repository locally (path to this clone is LOCAL_REPO below).
4. Run these commands:

    heroku apps:create HEROKU_APP
    cd LOCAL_REPO
    git remote add heroku git@heroku.com:HEROKU_APP.git
    git push heroku master
    heroku ps:scale web=1
    heroku ps:scale archivist=1
    heroku open

## Installation on fresh install of Ubuntu Linux 14.04 and Postgres

TODO: update these instructions after heroku migration

AWS: set up RDS Postgres instance and EC2 Ubuntu instance

Postgres:

    CREATE TABLE facts (
        id serial primary key,
        topic character varying(255),
        ts timestamp without time zone,
        content json
    );

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

    