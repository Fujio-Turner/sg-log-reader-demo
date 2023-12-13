## Step 3. - Processing the Log File

Let's parse the `sg_info.log` file. 


<!-- tabs:start -->

#### **Windows**

Open up a terminal and  `cd` command into the directory of the sg-log-reader downloaded folder and run the file pointing to the config.json

```console
sg-log-reader.exe config.json
```

#### **macOS**

Coming Soon

<!-- tabs:end -->


 **NOTE:** `sg_info.log` file that is large , 100MB+ and/or more have a lot of unique WebSocket information will take a long time to process.

###### More Notes
I recently added Async to the script so you might get weird errors because it proccessing lots of websocket IDs at onec. It <i>Should</i> be ok :-|