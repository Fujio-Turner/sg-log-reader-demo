## Step 2. - Install & Configure

## Download the SG-Log-Reader-demo 

From the github.com/fujio-turner/sg-log-reader-demo repo

Click here to [Back To: SG Log Reader Demo - Github Repo](https://github.com/fujio-turner/sg-log-reader-demo)
You can clone the repo or just download it as a zip file and unzip it too.
```console
git clone https://github.com/Fujio-Turner/sg-log-reader-demo.git
```
OR

Download the as a ZIP file

<img title="Download Github Code as a Zip" alt="Download Github Code as a Zip" src="https://helpdeskgeek.com/wp-content/pictures/2021/06/11CodeButtonDownloadZip.png">


## Install 

Python Virtual Environment:
[https://pypi.org/project/pipenv/](https://pypi.org/project/pipenv/)

or 

Homebrew install

```console
# brew install pipenv
```
Now open up a terminal and `cd` to the folder that you downloaded the sg-log-reader-demo into.

Once your in the above folder running this code by creating a Python Virtual Environment

```console
# pipenv shell 
```

Install some Python libaries that will run in in your virtual environment.

```console
# pipenv install couchbase
# pipenv install flask
# pipenv install icecream
```


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