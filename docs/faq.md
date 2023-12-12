### FAQ


+ What version of Python do I need ? +

  Python 3.6+

+ Is there any configuration to the script ? +

  Yes, there is a config.json file that you can update with things like credentials to a Couchbase bucket.


+ Is What version of SG logs will it work on ? +

  Its been testing with SG version 2.8.x to 3.0.1. Sorta works with 3.1.x

+ Is there any configuration to the script ? +

  Yes, there is a config.json file that you can update with things like credentials to a Couchbase bucket.


  + What is the `sg_info.log` ? +

  Its a file with the current general history of SG's general process and Websocket connection information from devices (CBL) to help debug issues.


  + Where do I get this `sg_info.log` from ? Where is it at ? +

  The default location for the SG log files are `/home/sync_gateway/logs/` there you will find `sg_info.log` OR do a [_sgcollect_info](https://docs.couchbase.com/sync-gateway/current/rest-api-admin.html#/Server/post__sgcollect_info) locally on the running SG machine and it will create a zip with a bunch of SG logs and in it `sg_info.log` is also included.

  + If I have 2 or more SGs behind a load balancer can I process them together and see the results in the dashboard ? +

  Yes you can be they will have different Websocket IDs. In the `config.json` there is a field to seperate the source. `"log-name":"test-today-node-0",  ///Optional: if you process multiple SG nodes you can tag the logs source here.` But there currently no way in the Dashboard to see which logs are from which SG node.

