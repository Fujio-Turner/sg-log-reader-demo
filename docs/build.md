
### Requirements:

- Python 3.6 or greater

## Download the SG-Log-Reader-demo 

## STEP 1
From the github.com/fujio-turner/sg-log-reader-demo repo

Click here to [Back To: SG Log Reader Demo - Github Repo](https://github.com/fujio-turner/sg-log-reader-demo)
You can clone the repo or just download it as a zip file and unzip it too.
```console
git clone https://github.com/Fujio-Turner/sg-log-reader-demo.git
```
OR

Download the as a ZIP file

<img title="Download Github Code as a Zip" alt="Download Github Code as a Zip" src="https://helpdeskgeek.com/wp-content/pictures/2021/06/11CodeButtonDownloadZip.png">


## STEP 2
## Install 

Python Virtual Environment:
[https://pypi.org/project/pipenv/](https://pypi.org/project/pipenv/)

or 

Homebrew install

```console
# brew install pipenv
```
Now open up a terminal and `cd` to the folder that you downloaded the sg-log-reader-demo into.

Once you are in the above folder run this code to create a Python Virtual Environment

```console
 pipenv shell 
```

Install some Python libaries that will run in in your virtual environment.

```console
 pipenv install couchbase
 pipenv install flask
 pipenv install icecream
```


[HOW TO: Configure JSON](/install)


## STEP 3

```console
 python3 sg-log-reader.py config.json
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


## STEP 4
To get to the dashboard to see stats you will run a local Python Flask Web Server. Run the command below to start the web server.

```console
 python3 app.py config.json
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