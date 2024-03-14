## Step 2. - Install & Configure

### Download Executables

Click here to [SG Log Reader Demo - Github Repo: Releases](https://github.com/Fujio-Turner/sg-log-reader-demo/tree/master/releases)


<!-- tabs:start -->

#### **macOS**

Download all three files into your local folder.
  - sg_log_reader
  - app  
  - config.json

#### **Windows**

Coming Soon
In the main repo in the `releases\{version}` folder there are Windows(.exe).

Download all three files into your local folder.
  - sg_log_reader.exe
  - app.exe  
  - config.json



<!-- tabs:end -->


## Configure

Update the config.json with your CB settings and path to your `sg_info.log` file:

<b>What</b>  and <b>Where</b> is a `sg_info.log` file? 
<br>
A: Click Here: [FAQ - sg_info.log](/faq)


 ```json
 {
"file-to-parse":"sg_info.log",	        /// "/path/to/file/here/sg_info.log" 
"cb-cluster-host":"127.0.0.1",          /// CB SERVER Hostname HERE
"cb-bucket-name":"sg-log-reader",       /// CB Bucket Name HERE: sg-log-reader._default._default
"cb-bucket-user":"Administrator",       ///  CB Bucket RBAC Username
"cb-bucket-user-password":"fujiofujio", /// CB Bucket RBAC Password
"cb-expire":86400,                         /// Optional: Data will expire in 24 hours
"log-name":"test-today-node-0",            /// Optional: if you process multiple SG nodes you can tag the logs source here.
"dt-log-line-offset":0,                    /// Optional: Sometime Windows Machine add address spaces in the timestamp in front.
"debug":false
}
 ```