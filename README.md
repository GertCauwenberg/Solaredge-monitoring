# Solaredge-monitoring
A project to monitor your new Solaredge inverter

This project builds on solaredge-local (https://github.com/drobtravels/solaredge-local), and therefore will only work for inverters supported by that project. As a reminder, "The local API is available on the SExxxxH-US models with SetApp as well as European three phase inverters SEXXK-XXXTXBXX4 models with SetApp like SE3K-E10K, SE12.5K-SE27.6K and SE33.3K". Basically, if your Solaredge inverter does NOT have a display, you're probably good for the solaredge-local library. Moreover, this project currently focuses on single-phase inverters.

The purpose of the project is to interrogate your inverter and optimizers regularly, aproximate the data that the solaredge-local library does not provide, save it to a local database, and upload the data to a site such as pvoutput.org. Sounds simple enough, and there is more than one way to do this. However, one of the advantages of a power optimizer is that you can have multiple panel orientations in one string. And in that case, you might want, just like me, to see the generated power for each orientation separately. This is where this script shines - if you want, you can upload every panel to a different system on PVOutput, or make any combination you want.

Setup is quite simple:
- create a database
- create the tables with the database.sql script
- copy the file config-sample.py to config.py
- fill in the configuration in config.py
- add a line in your crontab file, I'm using
    "*/5 5-21 * * *  YOURPATH/fetch.py 1>>YOURLOGPATH/`/bin/date +\%Y\%m\%d`.log  2>&1
- wait and look at the data pouring in :-)

Note - nothing will be recorded if your panel isn't producing anything. 03:00 AM is not the right time to run this :-)

Once all your panels have recorded at least one update you are ready for the next step:
- run upload.py once manually - it will ask you for each of your panels to which PVOutput system you want to upload its production.
- add a second row in your crontab file, something like
    "*/5 5-21 * * *  YOURPATH/upload.py 1>>YOURLOGPATH/`/bin/date +\%Y\%m\%d`.log  2>&1
- Look at those nice graphs appearing on PVOutput
