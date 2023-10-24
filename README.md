# sg-log-reader-demo

Version 2.0

Couchbase Mobile 2.x and greater now communicates via WebSockets.

This means its easier to track a mobile users replication to see "Why is sync is slow?" or "Why is it not syncing?"

The sg-log-reader tool take your SG log file parses it and puts it into a Couchbase Server bucket to query from.

You just need to:
 1. pick a sg_info.log for the python script to process.
 2. Have acccess to a CB Cluster for the script to insert data into.
 3. Open up the included index.html and pick a Begin and End Date to query

 It will:
   Output all the Sync Gateway database
   Output a list of names of all device users.
   Output a graph of all the synced that happen from the: Begin & Date you picked.
   You can pick a specific user to drill down to.
   you can pick a specific sync for a specific user.


Requirements:
Couchbase Bucket called: `sg-log-reader`.`_default`.`_default`
Couchbase Cluster With Index and Query Service
Web Browser


**HOW TO USE**

**RUNNING**

-Just run the pythen script and tell it where the sync_gateway_error.log is
```
#python3 sg-log-reader.py config.json
```

**FAQ**

**Q:** What do I need to use this fantansic tool?


**A:**

-Python 3.6+ installed 

-Have a Couchbase Server with Data , Index & Query


**Q:** Is there any configuration to the script?


**A:**

Yes, there is a config.json file that you can update with things like creditals to a Couchbase bucket

#Works on My Computer Tested & Certified ;-)