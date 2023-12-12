
### Using The Dashboard

#### Search
In the upper left hand corner there are two input boxes with a datetime range with a `FROM:` datetime and `TO:` datetime. This helps to narrow the search of the SG logs your interested in.

* The dashboard will auto pre-populate 
   - FROM DateTime input box (newest time record in the `sg_info.log` file) 
   - TO DateTime input box , an hour back from the above DateTime.
   - It will pre select a SG DB name too.


##### View By (All | Seconds | Minutes)
There might be many thousands of stats. So much so that plotting all of them will create web browser memory and CPU issues i.e. slow dashboard. To prevent this by default the stats in the charts are show `Group By: Seconds`. So every value on the x-axis shows everything in that one second time frame. You can also show all the entries OR group by minute too.

#### Filters

Be default the charts after clicking the <button>Search</button> button will show you all the results. You can filter the results by

- Pulled: ALL Results , Fully Sync , Missing Docs Sync or Fully Sync (but no new changes)
- Pushed: CBL Pushed Docs: ALL Results , Sync with None or Some
- Pulled: New vs Old Sync via (since = Zero)
- Length of Time CBL Connected (seconds)**
- \# of _changes <i>(possible changes)</i> to sync (integer)
- Conflicts in Sync: True
- Errors in Sync: True

**This does not necessarily mean how long it took to sync.

##### Zoom-In & Pan (drag: left or right) - Charts
You can click on the line charts and PAN left or right by dragging it. If you hold down the `SHIFT` and select in the chart it will create a `zoom` box for you pick a section of the chart your more interesting in. There is a `Zoom Reset` button on the left. The two line charts will adjust themselves to the new x-axis on zoom and/or pan too.

#### Picking a Specific User

##### User List:

On the left it will show you all the SG users who made connections in the DatesTime window selected above plus how many times they connected in that time window. 
You can sort the list alphabetically(default) or by most number of connections per user.

##### Click User Name:
Just click the name of the user and it will pre populate the filter by username input box ,above, and then just click <button>Search</button> to filter and populate charts and stats for that user only.

***note*** When you pick and <button>Search</button> by a users the chart will plot `All Entries` on the x-axis regardless if you didn't change the `view by` dropdown value.

##### User Details:

Once you <button>Search</button> by a user on the bottom it will show you all the indivudal replication events for that user for that DateTime. If you click on the row it will show the full raw SG log for the WebSocket ID.

#### Bugs & New Feature Requests

If you are wanting a new feature or there is a bug click here to report it: [SG Log Reader Demo - Issues](https://github.com/Fujio-Turner/sg-log-reader-demo/issues)