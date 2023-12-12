## Step 3. - Processing the Log File

Let's Parse the log file. Run the command below in the directory of the sg-log-reader downloaded folder

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
 **NOTE:** `sg_info.log` file that is large , 100MB+ and/or more have a lot of unique WebSocket information will take a long time to process.

After you get the above `Done - Per wsId: ...` data should be in your Couchbase bucket.

###### More Notes
I recently added Async to the script so you might get weird errors because it proccessing lots of websocket IDs at onec. It <i>Should</i> be ok :-|