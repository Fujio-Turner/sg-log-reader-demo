
# SG Log Reader Demo





<div class="grid-container">
  <div class="grid-item">
    I created this tool to be able to debug SG issue by getting a local copy of a SG's `sg_info.log` file and parsing it on my local machine to see whats going on in the SG. There are two parts to this script.

<div>
1. Parse and process the `sg_info.log` file and inserting the results in to a CB bucket.
<br>
2. Run a local web server to view an interactive dashboard of the results.
</div>

&#8678; Go through all the <b> Steps 1 to 4 </b> on the left side bar <b>or</b> bottom links to the <i>next page</i> to get up and running.

- SG = Sync Gateway
- CBL = Couchbase Lites
- CB = Couchbases
  
  </div>
  <div class="grid-item">
   <img src="img//sg-log-reader-2.0.png" alt="Dashboard" height="300px">
  </div>
  <div class="grid-item">
<b>NEW</b>

version 2.1.0
- macOS executable

Future - More
In the future this will do more features to better understand other things going on inside SG. If you are wanting a new feature or there is a bug click here to report it: [SG Log Reader Demo - Issues](https://github.com/Fujio-Turner/sg-log-reader-demo/issues)
  
  </div>
  <div class="grid-item">
  <b>Notes</b>

-- Its advised to "Flush" the Couchbase Bucket for each new SG environments you process. Example: Dev , QA or Prod so you don't get them mixed results in the dashboard.

-- Logs from a SG machine running on MS Windows might have issues as its timestamps in the logs might have a different format thus effecting the processing of SG file.
  </div>

  <!-- Add more divs as needed -->
</div>

Click here to [Back To: SG Log Reader Demo - Github Repo](https://github.com/fujio-turner/sg-log-reader-demo)

Works on My Computer Tested & Certified ;-)