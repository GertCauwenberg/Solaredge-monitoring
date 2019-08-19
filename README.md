# Solaredge-monitoring
A project to monitor your new Solaredge inverter

This project builds on solaredge-local (https://github.com/drobtravels/solaredge-local), and therefore will only work for inverters supported by that project. As a reminder, "The local API is available on the SExxxxH-US models with SetApp as well as European three phase inverters SEXXK-XXXTXBXX4 models with SetApp like SE3K-E10K, SE12.5K-SE27.6K and SE33.3K". Basically, if your Solaredge inverter does NOT have a display, you're probably good for the solaredge-local library. Moreover, this project currently focuses on single-phase inverters.

The purpose of the project is to interrogate your inverter and optimizers regularly, aproximate the data that the solaredge-local library does not provide, save it to a local database, and upload the data to a site such as pvoutput.org. The catch is, not all panels have the same orientation - so I want a total per orientation, not just the grand total of the whole system.

Setup is quite simple:
- create a database
- create the tables with the database.sql script
- fill in the configuration in fetch.py
- add a line in your crontab file, I'm using
    "*/5 5-21 * * *  YOURPATH/fetch.py 1>>YOURLOGPATH/`/bin/date +\%Y\%m\%d`.log  2>&1
- wait and look at the data pouring in :-)
