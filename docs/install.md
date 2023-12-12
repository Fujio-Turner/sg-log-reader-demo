## Step 2. - Install & Configue

### Install 

Python Virtual Environment:
[https://pypi.org/project/pipenv/](https://pypi.org/project/pipenv/)

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


## Configure

Update the config.json with your CB settings and path to your `sg_info.log` file:

 ```json
 {
"file-to-parse":"sg_info.log",	    ///   "/path/to/file/here/sg_info.log" 
"cb-cluster-host":"127.0.0.1",      /// CB SERVER Hostname HERE
"cb-bucket-name":"sg-log-reader",   /// CB Bucket Name HERE: sg-log-reader._default._default
"cb-bucket-user":"Administrator",   ///  CB Bucket RBAC Username
"cb-bucket-user-password":"fujiofujio", /// CB Bucket RBAC Password
"cb-expire":86400,                 ///Optional: Data will expire in 24 hours
"log-name":"test-today-node-0",  ///Optional: if you process multiple SG nodes you can tag the logs source here.
"dt-log-line-offset":0,          ///Optional: Sometime Windows Machine add address spaces in the timestamp in front.
"debug":false
}
 ```

 [Go to Step 3. - Processing the Log File](/process)