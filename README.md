# sg-log-reader-demo

Tired of combing through Sync Gateway logs? .... OUCH!

Trying to find the _changes that is just too slow?  ... Yes sir e

Just use the new and improved SG-LOG-READER and parse through those pesky logs lickety split.

**FAQ**

**Q:** How dose the SG-LOG-READER work?

**A:** It goes line by line looking for the nuggets of information you need so you don't have to.

-Just run the pythen script and tell it where the sync_gateway_error.log is
```
#/path/to/sg-log-reader.py /path/to/your/sync_gateway_error.log > test.json
```
-Open the test.json file and copy/paste that JSON

-Start a local web server with the included index.html 

-Paste that JSON into the textarea box and click "Make Graph".


**Q:** What do I need to use the fantansic tool?

**A:**

-Python 2.6+ installed 

-Local Web Server ,example [MAMP](https://www.mamp.info/en/) , for the index.html file.



#Works on My Computer Tested & Certified ;-)
