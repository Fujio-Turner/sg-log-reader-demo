# sg-log-reader-demo
Version 2.0

![Dashboard](img/sg-log-reader-2.0.png)

Couchbase Mobile 2.x and greater now communicates via WebSockets.

This means its easier to track a mobile users replication to see "Why is sync is slow?" or "Why is it not syncing?"

The sg-log-reader tool take your SG log file ,sg_info.log, parses it and puts it into a Couchbase Server bucket to query from.

You just need to:
 1. pick a sg_info.log for the python script to process.
 2. Have acccess to a CB Cluster for the script to insert data into.
 3. Open up the included index.html and pick a Begin and End Date to query
 4. Have pipenv installed

 It will:
   Output all the Sync Gateway database
   Output a list of names of all device users.
   Output a graph of all the synced that happen from the: Begin & Date you picked.
   You can pick a specific user to drill down to.
   you can pick a specific sync for a specific user.


###Requirements:
Couchbase Bucket

Couchbase Cluster With Index and Query Service

Create the below index.

```
CREATE INDEX `userSyncFinder_v6` ON `sg-log-reader`(`dt`,`user`,`sgDb`,`dtDiffSec`,`sentCount`,`errors`,`tRow`,`since`,array_length(`filterBy`),`conflicts`,`pushAttCount`,`pullAttCount`,`pushCount`,`qRow`,`cRow`,`blipC`) WHERE ((`docType` = "byWsId") and (`orphane` = false))
```
NOTE: if you put the data in a different bucket then `sg-log-reader` change the above to match your bucket name.


Install 

Python Virtual Environement.
https://pypi.org/project/pipenv/

or 

Homebrew install

```console
# brew install pipenv
```

Running the code by creating a Python Virtual Environment

```console
# pipenv shell 
```

Install some Python libaries that will run in in your virtual environment.

```console
# pipenv install couchbase
# pipenv install flask
# pipenv install icecream
```

Update the config.json with:

 ```json
 {
"log-name":"test-today-node-0",
"file-to-parse":"sg_info.log",	    ///   "/path/to/file/here/sg_info.log" 
"cb-cluster-host":"127.0.0.1",      /// CB SERVER Hostname HERE
"cb-bucket-name":"sg-log-reader",   /// CB Bucket Name HERE , _default (scope&collection)
"cb-bucket-user":"Administrator",   ///  CB Bucket RBAC Username
"cb-bucket-user-password":"fujiofujio", /// CB Bucket RBAC Password
"dt-log-line-offset":0,
"debug":false
}
 ```

Let's Parse the log file. Run the command below in the dictory of the sg-log-reader download folder

```console
 # python3 sg-log-reader.py config.json
```

 The output should look like this below:


```console
Starting - Reading Data File:  2023-11-05 09:43:35.072700
Number - Lines in log file:  766836
Number - WebSocket Connections:  18585
Done - Reading Data File:  2023-11-05 09:43:37.112688
Starting - Per wsId :  2023-11-05 09:43:37.112698
Done - Per wsId :  2023-11-05 09:48:19.576021
```

**NOTE sg_info.log that is large, 100MB and/or have alot of websocket information will take a long time to process.

After you get the above `Done - Per wsId: ...` data should be in your couchbase bucket now.

To get to a dashboard to see stats you'll run a local python Flask Web Server via

```console
# python3 app.py
```

OUTPUT should look something like this.

```console
 * Serving Flask app 'app'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:8080
 * Running on http://192.168.0.193:8080
```

Now open up a Web Browse and go to:

[http://127.0.0.1:8080](http://127.0.0.1:8080)



It will pre-populate the newest datetime in the box and pick a SG DB.

Just click the Button(Search).




FAQ

**A:**

-Python 3.6+ installed 

-Have a Couchbase Server with Data , Index & Query


**Q:** Is there any configuration to the script?


**A:**

Yes, there is a config.json file that you can update with things like creditals to a Couchbase bucket

Works on My Computer Tested & Certified ;-)