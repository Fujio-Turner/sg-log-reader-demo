# SG Log Reader Demo
Version 2.0

![Dashboard](img/sg-log-reader-2.0.png)

## Why

Couchbase Mobile 2.x and greater now communicates via WebSockets.

This means it easier to track a mobile user's replication to see <i>"Why is sync is slow?"</i> or <i>"Why is it not syncing?"</i>. 

## What
The sg-log-reader tool takes your SG log file and parses them to:

* Aggregate

* Count 

* Sum

* and More 

It takes the above information and puts it into a Couchbase Server bucket to query for a built-in web dashboard (ABOVE IMAGE).

## How

#### Process
You just need to:

 1. Pick a `sg_info.log` for the python script to process.
 2. Have access to a CB Cluster for the script to insert data into.
 3. Go to (`http://127.0.0.1:8080`) to checkout the Dashboard above.
 
#### Result
 It will:
  - Output all the Sync Gateway's databases
  - Output a list of names of all device users.
  - Output a graph of all the synced that happen from the: Begin & DateTime you picked.
  - You can pick a specific user to drill down to.
    - pick a specific sync(s) for a specific user.


###### Click below to get started: 
### [Docs - SG Log Reader Demo](https://fujio-turner.github.io/sg-log-reader-demo/)