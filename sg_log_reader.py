import os
import sys
import json
from datetime import timedelta
from icecream import ic

import re
import datetime, time
import uuid
import cProfile
import pstats
import hashlib
import asyncio

import traceback

from couchbase.auth import PasswordAuthenticator
from acouchbase.cluster import Cluster
import couchbase.subdocument as SD
from couchbase.options import (ClusterOptions, ClusterTimeoutOptions, QueryOptions)
from couchbase.exceptions import CouchbaseException
from couchbase.exceptions import DocumentNotFoundException
from couchbase.collection import InsertOptions , UpsertOptions

#https://github.com/couchbase/docs-sdk-python/blob/release/3.1/modules/howtos/examples/caching_flask.py

class work():
    debug = []
    ### debug options: 
    ### "*" = all
    ### "wsId" = wsid log processing
    ### "cb" = couchbase ops
    ### "listMake" = anything related to making WsId list
    ### "listMakeRaw" = raw output of the file + counter
    cb = None
    sgLogName = "sg_info.log"
    cbHost = "127.0.0.1"
    cbUser = "Administrator"
    cbPass = "fujiofujio"
    cbBucketName = "sg-log-reader"
    cbScopeName = "_default"
    cbCollectionName = "_default"
    cbColl = None
    logData = []
    wsIdList = {}
    wasBlipLines = False
    blipLineCount = 0
    oldWsDic = {}
    sgDtLineOffset = 0
    sgLogTag = "default"
    logfile = None
    logFileName = "sg-log-reader.log"
    logFilePath = "logs/"
    logLineLen = 0
    logLineDepthLevel = 1000
    logLineDepthPercent = 0.02
    logNumberOflines = 1
    logScanDepthAfterClose = 50
    cbTtl = 86400

    def __init__(self, file):
        asyncio.run(self.main(file))

    def __del__(self):
        sys.stdout = sys.__stdout__

    async def main(self, file):
        await self.readConfigFile(file)
        await self.debugIceCream()
        await self.makeCB()
        await self.openSgLogFile()

    async def makeCB(self):
        try:
            auth = PasswordAuthenticator(self.cbUser, self.cbPass)
            cluster = Cluster('couchbase://'+self.cbHost, ClusterOptions(auth))
            await cluster.wait_until_ready(timedelta(seconds=5))
            bucket = cluster.bucket(self.cbBucketName)
            #bucket.scope(self.cbScopeName).collection(self.cbCollectionName)
            self.cbColl = bucket.default_collection()
            self.cb = await bucket.on_connect()
            return cluster, self.cb
        except CouchbaseException as ex:
            print("CB Connetion Error:", ex)
            ic("Error: Could not connect to CB Cluster: " , self.cbHost, " as: ", self.cbUser)
            exit()
    async def diffdates(self, d1, d2):
        return (time.mktime(time.strptime(d2, "%Y-%m-%dT%H:%M:%S")) - time.mktime(time.strptime(d1, "%Y-%m-%dT%H:%M:%S")))

    async def debugIceCream(self):
        if self.debug != []:
            ic.enable()
        else:
            ic.disable()

    async def readConfigFile(self,configFile):
        a = open(configFile, "rb" )
        b = json.loads(a.read())
        self.sgLogName = b["file-to-parse"]
        self.cbHost = b["cb-cluster-host"]
        self.cbBucket = b["cb-bucket-name"]
        self.cbUser = b["cb-bucket-user"]
        self.cbPass = b["cb-bucket-user-password"]
        self.debug = b["debug"]
        ##self.sgDtLineOffset = b["dt-log-line-offset"]
        self.sgLogTag = b["log-name"]
        self.cbTtl = b['cb-expire']
        a.close()

    async def openSgLogFile(self):
        index = 0	
        print("Opening SG Log File: ", self.sgLogName)
        print("Starting - Reading Data File: ", datetime.datetime.now())
        #with open(self.sgLogName, "r") as a:
        #	b = [line.strip() for line in a.readlines()]
        if os.path.exists(self.sgLogName):
            counter = 1
            with open(self.sgLogName, "r") as a:
                for x in a:
                    counter +=1
                    if "*" in self.debug or "makeListRaw" in self.debug:
                        ic(counter, x)
                    line = x.rstrip('\r|\n')
                    self.logData.append(line)
                    await self.importCheck(line)
                    await self.sqlCheck(line)
                    #await self.sgDb(line)  ## this is very noisey
                    await self.generalErrors(line)
                    await self.wsErrors(line)
                    #await self.replicateCheck(line)
                    await self.dcpChecks(line)
                    #await self.sgStarts(line)
                    if self.wasBlipLines == True:
                        await self.findWsId(line, index)
                    await self.findBlipLine(line, index)
                    index +=1
            self.logNumberOflines = counter
            self.logLineDepthLevel = counter * self.logLineDepthPercent
            print("Number - Lines in log file: ", counter)
            print("Number - WebSocket Connections: ", self.blipLineCount)
            print("Done - Reading Data File: ", datetime.datetime.now())
            if "*" in self.debug or "makeList" in self.debug:
                ic("makeListBig:",self.wsIdList)
                ic("Number - Lines in log file: ", counter)
                ic("Number - WebSocket Connections: ", self.blipLineCount)
               

            await self.getDataPerWsId()
        else:
            print("Error: File not found: ", self.sgLogName)
            exit()


    async def findBlipLine(self, x, lineNumb):

        if "/_blipsync" in x and "GUEST" not in x: 
            if "*" in self.debug or "makeList" in self.debug:
                ic("BlipLine: ", lineNumb, x)
            self.blipLineCount += 1
            userN = await self.getUserName(x)
            t = await self.getTimeFromLine(x)
            httpNum = await self.httpTransNum(x)
            k = httpNum+userN[1]
            isoDt = await self.iso8601_to_epoch(t[1])
            self.wsIdList[k] = {"user":userN[1], "sgDb":userN[0], "auth":False, "dt":t[0], "dtFullEpoch":isoDt, "http":httpNum}
            self.wasBlipLines = True
            if "*" in self.debug or "makeList" in self.debug:
                ic("BlipLine: ", self.wsIdList[k])

    async def findWsId(self, wsLine, index):
        if "Upgraded to BLIP+WebSocket protocol" in wsLine or "Upgraded to WebSocket" in wsLine:
            if "*" in self.debug or "makeList" in self.debug:
                ic("Find Blip Line: ", index, wsLine)
            c = re.findall(r"\[([A-Za-z0-9_]+)\]", wsLine)
            if len(c) > 1:
                #check if ws in new or old
                userN = await self.getUserNameBlip(wsLine)
                httpNum = await self.httpTransNumPlus(wsLine)
                if httpNum+userN in self.wsIdList:
                    bline = self.wsIdList[httpNum+userN]
                    if "ws" not in bline:
                        bline["ws"] = c[1]
                        bline["startLine"] = index
                        bline["auth"] = True
                        self.wsIdList[httpNum+userN] = bline
                        #self.wasBlipLines = False
                        #self.oldWsDic[c[1]] = True

        if " --> 401 Login required " in wsLine:
            self.wasBlipLines = False

    async def httpTransNumPlus(self, line):

        h = line.split(" HTTP+: ")
        r =  h[1].split(" ")
        if "#" in r[0]:
            return r[0] #PRE SG 3.1
        if "#" in r[1]:
            return r[1].replace(":", "")  #Post SG 3.1
        if "#" in r[2]:
            return r[2].replace(":", "")  #Post SG 3.1
        return ""

    async def httpTransNum(self, line):
        h = line.split("HTTP:")
        if h[1].split(" ")[1] != "":
            r = h[1].split(" ")[1]  #post-SG 3.1
            t = r.split("c:")[1]
        elif h[1].split(" ")[2] != "":
            t = h[1].split(" ")[2] #pre-SG 3.1
        else:
            t = ''
        return t


    async def getUserName(self, line):
    # Check if the expected pattern exists in the line
        if "<ud>" in line and "</ud>" in line:

                    # Pattern to match the database name between / and /_blipsync
            db_pattern = r'/([^/]+)/_blipsync'
            db_match = re.search(db_pattern, line)
            
            # Pattern to match the username between <ud> and </ud>
            user_pattern = r'<ud>(.*?)</ud>'
            user_match = re.search(user_pattern, line)
            
            if db_match:
                dbname = db_match.group(1)
            
            if user_match:
                username = user_match.group(1)

            return [dbname, username]

        else:

            # Fallback to splitting method if pattern not found
            c = line.split(" ")
            sgDb = c[6].split("/")[1]
            usrN = c[-1].rstrip(')')
            return [sgDb, usrN]
 

    async def getUserNameBlip(self, line):
        #c = re.findall(r"\(([A-Za-z0-9_]+)\)", line)
        if "<ud>" in line and "</ud>" in line:
            pattern = r'<ud>(.*?)</ud>'
            #pattern = r'\(as <ud>(.*?)</ud>\)'
            # Use re.search to find the first match for the pattern in the log line
            match = re.search(pattern, line)
            # If a match is found, print the matched string
            if match:
                return match.group(1)

        c = line.split(" ")
        if len(c) == 20:
            return c[16].rstrip(')')
        else:
            if c[15] != "":
                d = c[15].rstrip('.')
                return d.split(":")[1]
            if c[16] != "":
                return c[16].rstrip(')')

    async def getDataPerWsId(self):
        print("Starting - Per wsId : ", datetime.datetime.now())
        list_of_tasks = []
        for key, x in self.wsIdList.items():
            list_of_tasks.append(self.getDataPerWsIdWorker(x))
        result = await asyncio.gather(*list_of_tasks, return_exceptions=True)

        for idx, res in enumerate(result):
            if isinstance(res, BaseException):
                # Handle the exception (e.g., log the error, retry the task, etc.)
                print(f"Task {idx} raised an exception: {res}")
            #else:
                # Process the result
            #	print(f"Task {idx} returned: {res}")

        print("Done - Per wsId :", datetime.datetime.now())


    async def getDataPerWsIdWorker(self, x):
        sinceList = []
        if x["auth"] == True:
            w = x["ws"]
            r = await self.loopLog(x["ws"], x["startLine"], sinceList)
            tf = await self.getTimeFromLine(r[0][0])
            tl = await self.getTimeFromLine(r[0][-1])

            if r[1] is not None:
                sinceList.append(r[1])
            tRow = 0
            if r[2] is not None:
                tRow = r[2]
            if r[3] is not None:
                tRow = tRow + r[3]
            if tf[0] is not None and tl[0] is not None:
                df = await self.diffdates(tf[0],tl[0])
            else:
                df = None
            isoDt = await self.iso8601_to_epoch(tf[1])
            d = {
                "docType": "byWsId",
                "user": x["user"],
                "sgDb": x["sgDb"],
                "sgColl": {},				
                "dtFullEpoch": isoDt,
                "dt": tf[0],
                "dtEnd": tl[0],
                "dtDiffSec": df,
                "since": sinceList,
                "continuous": r[8],
                "conflicts": r[9],
                "errors": r[10],
                "warnings": r[11],
                "cRow": r[2],
                "qRow": r[3],
                "tRow": tRow,
                "attSuccess": r[15],
                "pullAttCount": r[17],
                "pushCount": r[14],
                "pushProposeCount": r[18],
                "pushAttCount": r[13],				
                "sentCount": r[12],
                "filterBy": r[5],
                "changesChannels": r[16],
                "logTag": self.sgLogTag,
                "blipC": r[6],
                "blipO": r[7],
                "auth": True,
                "orphane": False,
                "log": r[0]
            }
        else:
            hash_object = hashlib.md5()
            hash_object.update(str(x).encode())
            #w = str(uuid.uuid1())
            w = hash_object.hexdigest()
            d = {
                "docType": "byWsId",
                "user": x["user"],
                "sgDb": x["sgDb"],
                "sgColl": {},	
                "dtFullEpoch": x['dtFullEpoch'],
                "dt": x['dt'],
                "rRow": 0,
                "qRow": 0,
                "tRow": 0,
                "logTag": self.sgLogTag,
                "auth": False,
                "orphane": True,
                "log": []
            }
        asyncio.create_task(self.cbUpsert(w, d, self.cbTtl))
        return [w, d]

                    
    async def loopLog(self, wsId, startLogLine, sinceList):
        logLine = []
        channelRow = 0
        queryRow = 	0
        conflictCount = 0
        errorCount = 0
        warningCount = 0
        sent = 0
        pullAttCount = 0
        attSuc = 0
        pushCount = 0
        pushProposeCount = 0
        pushAttachCount = 0
        since = None
        filterBy = False
        blipClosed = False
        blipOpened = False
        filterByChannels = []
        changesChannels = {}
        continuous = None
        passIt = 0
        wsProcData = {
                    'logLine': [],
                    'channelRow': 0,
                    'queryRow': 0,
                    'conflictCount': 0,
                    'errorCount': 0,
                    'warningCount': 0,
                    'sent': 0,
                    'pullAttCount': 0,
                    'attSuc': 0,
                    'pushCount': 0,
                    'pushProposeCount': 0,
                    'pushAttachCount': 0,
                    'since': None,
                    'filterBy': False,
                    'blipClosed': False,
                    'blipOpened': False,
                    'filterByChannels': [],
                    'changesChannels': {},
                    'continuous': None,
                    'passIt': 0
                    }
        
        crudPattern = r"\sCRUD:\sc:\[[a-f0-9]+\]\s"

        #for x in self.logData[startLogLine:]:
        for a in range(startLogLine, self.logNumberOflines):
            x = self.logData[a]

            if wsId in x and "WS" not in x:
                if "*" in self.debug or "wsId" in self.debug:
                    ic("WSID found in line : ", wsId, x)
                if blipClosed is False:
                    passIt = 0
                cleanLine = x.rstrip('\r|\n')
                logLine.append(cleanLine)

                #_changes making
                if "GetCachedChanges(\"" in x:
                    c = await self.changeCacheCount(x)
                    channelRow = channelRow + c[0]
                    changesChannels[c[1]] = True
                    continue
                if "GetChangesInChannel(" in x:
                    d = await self.changeQueryCount(x)					
                    queryRow = queryRow + d[0]
                    changesChannels[d[1]] = True
                    continue

                if "rows from query for " in x:
                    d = await self.changeQueryCountByRow(x)					
                    queryRow = queryRow + d[0]
                    changesChannels[d[1]] = True
                    continue

                if " Continuous:" in x and " SyncMsg:" in x:
                    continuous = await self.findContinuous(x)

                if "Filter:sync_gateway/bychannel" in x:
                    filterBy = True
                    filterByChannels = await self.findChannelsList(x)

                if " changes to client, from seq " in x:		
                    j = await self.findSentCount(x)
                    sent = sent + j
                    continue
                if " proveAttachment successful for doc " in x:		
                    attSuc += 1
                    continue
                if "Type:getAttachment Digest:" in x:		
                    pullAttCount += 1
                    continue

                #push from CBL 
                if "Type:proposeChanges" in x:
                    p = await self.findPushCount(x)
                    pushProposeCount = pushProposeCount + p
                    continue

                if "Added attachment" in x and "CRUD:" in x:
                    pushAttachCount +=1
                    continue

                if re.search(crudPattern, x):
                    pushCount += 1
                    continue

                if "409 Document update conflict" in x:
                    conflictCount += 1
                    continue
                if "[ERR]" in x or "Error retrieving changes for channel" in x:
                    errorCount += 1
                    continue

                if "Error " in x and ".go:" in x and "[WRN]" not in x: 
                    # for 'revocation' changes feed errors
                    errorCount += 1
                    continue

                if 'error' in x.lower():
                    errorCount += 1

                if "[WRN]" in x:
                    warningCount += 1
                    continue				
                #beginning and end
                if "BLIP+WebSocket connection closed" in x:
                    passIt = self.logLineDepthLevel - self.logScanDepthAfterClose
                    blipClosed = True
                    continue
                if "Upgraded to" in x and "WebSocket protocol" in x:
                    blipOpened = True
                    continue
                
                if "Since:" in x and "SyncMsg:" in x:
                    if "Since:0 " in x:  #looks for _change since=0
                        since = "0"
                    else:
                        since = await self.findSince(x)

            else:
                passIt += 1
            if passIt >= self.logLineDepthLevel:
                filterByChannels.sort()
                changesChannels = sorted(changesChannels.keys())
                return [logLine, since, channelRow, queryRow, filterBy, filterByChannels, blipClosed, blipOpened, continuous, conflictCount, errorCount, warningCount, sent, pushAttachCount, pushCount, attSuc, changesChannels, pullAttCount,pushProposeCount]
        filterByChannels.sort()
        changesChannels = sorted(changesChannels.keys())
        return [logLine, since, channelRow, queryRow, filterBy, filterByChannels, blipClosed, blipOpened, continuous, conflictCount, errorCount, warningCount, sent, pushAttachCount, pushCount, attSuc, changesChannels, pullAttCount,pushProposeCount]

    async def changeCacheCount(self, line):
        a = line.split(" ")
        ic(a)

        b = line.split('GetCachedChanges("')

        match = re.search(r'<ud>\d+\.<ud>(.*?)</ud></ud>', b[1]) #POST SG 3.1
        
        if match:
            return [int(a[8]),match.group(1)]
        
        c = b[1].split('"')
        
        
        if a[7] == "got":
            return [int(a[8]),c[0]]
        else:
            return [int(a[7]),c[0]]

    async def changeQueryCount(self, line):
        a = line.split(" ")
        ic(a)

        if "<ud>" in a[5]:
            match = re.search(r'<ud>\d+\.<ud>(.*?)</ud></ud>', a[5])  # POST SG 3.1

            if match:
                return [int(a[7]),match.group(1)]
        else:

            b = line.split('GetChangesInChannel("')  # PRE SG 3.1
            c = b[1].split('"')
            return [int(a[6]),c[0]]
        

    async def changeQueryCountByRow(self,line):
        number = re.search(r'Got (\d+) rows', line).group(1)  
        # Extracting the double-quoted string using regular expression
        quoted_string = re.search(r'for "([^"]+)"', line).group(1)  
        return [int(number), quoted_string]


    async def getTimeFromLine(self, line):
        return [line[0+self.sgDtLineOffset:19+self.sgDtLineOffset].rstrip("-"), line[0+self.sgDtLineOffset:24+self.sgDtLineOffset].rstrip("-")]

    async def sgStarts(self, x):
        if "==== Couchbase Sync Gateway/" in x:
            t = await self.getTimeFromLine(x)
            d = {"docType":"sgStart","dt":t[0], "tag":self.sgLogTag}
            self.cbUpsert(self.sgLogTag+"::sgStart::"+t[0], d, self.cbTtl)


    async def dcpChecks(self, x):
        if "DCP:" in x:
            if "*" in self.debug or "makeList" in self.debug:
                ic("DCP:", x)
            t = await self.getTimeFromLine(x)
            if "error" in x or "Error" in x:
                if "*" in self.debug or "makeList" in self.debug:
                    ic("DCP:", t[0], x)
                e = await self.errorTempDoc(t[0], t[1], "dcp")
                return e

    async def importCheck(self, x):
        if "Import:" in x:
            if "*" in self.debug or "makeList" in self.debug:
                ic("Import:", x)
            t = await self.getTimeFromLine(x)
            if "error" in x or "Error" in x:
                if "*" in self.debug or "makeList" in self.debug:
                    ic(t[0], x)
                r = await self.errorTempDoc(t[0], t[1], "import")
                return r
    
    async def sqlCheck(self, x):
        if "Query:" in x:
            if "*" in self.debug or "makeList" in self.debug:
                ic("Query:", x)
            t = await self.getTimeFromLine(x)
            if "error" in x or "Error" in x:
                if "*" in self.debug or "makeList" in self.debug:
                    ic("Query:", t[0], x)
                r = await self.errorTempDoc(t[0], t[1], "query")
                return r	

    async def sgDb(self, x):
        if " db:" in x or " db." in x:
            t = await self.getTimeFromLine(x)
            if "error" in x or "Error" in x:
                ic(t[0], x)
                r = await self.errorTempDoc(t[0], t[1], "sgDb")
                return r			

    async def wsErrors(self, x):
        if " WS: " in x:
            if "*" in self.debug or "makeList" in self.debug:
                ic("WS Error:",x)
            t = await self.getTimeFromLine(x)
            if "error" in x or "Error" in x:
                if "*" in self.debug or "makeList" in self.debug:
                    ic("WS Error:", t[0], x)
                r = await self.errorTempDoc(t[0], t[1], "ws")
                return r	

    async def generalErrors(self, x):
        if "[ERR]" in x:
            if "*" in self.debug or "makeList" in self.debug:
                ic("SG Process Error",x)
            t = await self.getTimeFromLine(x)
            if "error" in x or "Error" in x:
                if "*" in self.debug or "makeList" in self.debug:
                    ic("SG Process Error:", t[0], x)
                r = await self.errorTempDoc(t[0], t[1], "gen")
                return r	

    async def errorTempDoc(self, dt, dtFullEpoch, errorElement):
        key = dt + "::errors"
        d = await self.cbGet(key)
        if d is not False:
            #Check if doc exists
            d[errorElement] += 1
            e = await self.cbUpsert(key, d, self.cbTtl)
            return e
        else:
            #if not create Template
            isoDt = await self.iso8601_to_epoch(dtFullEpoch)
            j = {"docType":"sgErrors", "dt":dt, "dtFullEpoch":isoDt, "import":0, "dcp":0, "query":0, "sgDb":0, "ws":0, "gen":0}
            j[errorElement] += 1
            f = await self.cbInsert(key, j, self.cbTtl)
            return f

    async def findSentCount(self, x):
        a = x.split(" ")
        ic(a)
        if a[5] == "Sent":
            return int(a[6])  #Post SG 3.1
        else:
            return int(a[5])  #Pre SG 3.1
    
    async def findPushCount(self, x):
        a = x.split("#Changes: ")
        ic(a)
        return int(a[1])
    
    async def n1qlQueryInfo(self, x):

        if "Query: N1QL Query" in x:

            t = await self.getTimeFromLine(x)
            a = x.split(" ")
            b = await self.n1qlTimeSplit(a[6])
            c = {"q":a[4], "t":a[6], "dt":t[0], "tChop":b, "tag":self.sgLogTag}
            d = {"docType":"query", "q":[c]}
            ic(b)
            await self.cbSubDocAppend(self.sgLogTag+"::query::"+t[0], 'q', b, self.cbTtl)

            """
            try:
                r = self.cbColl.mutate_in(self.sgLogTag+"::query::"+t[0], (SD.array_append('q',b),))
                ic(r)
                return r
            except DocumentNotFoundException:
                r = self.cbInsert(self.sgLogTag+"::query::"+t[0],d,self.cbTtl)
                ic(r)
                return r
            except CouchbaseException:
                ic(traceback.format_exc())
                ic("Error: Inserting Key: ","sgStart::"+t," maybe already in bucket")
            
            """



        if "Channel query" in x:

            t = await self.getTimeFromLine(x)
            a = x.split(" ")			
            b = await self.n1qlTimeSplit(a[5])
            c = {"q":a[3], "t":int(a[8]), "chan":a[12], "dt":t[0], "st":a[14], "end":a[16], "tChop":b, "tag":self.sgLogTag}
            d = {"docType":"query", "q":[c]}

            self.cbSubDocAppend(self.sgLogTag+"::query::"+t[0], 'q', b, self.cbTtl)

            """
            try:
                r = self.cbColl.mutate_in(self.sgLogTag+"::query::"+t[0], (SD.array_append('q',b),))
                ic(r)
                return r
            except DocumentNotFoundException:
                    r = self.cbInsert(self.sgLogTag+"::query::"+t[0],d,self.cbTtl)
                    ic(r)
                    return r
            except CouchbaseException:
                ic(traceback.format_exc())
                ic("Error: Inserting Key: ","sgStart::"+t," maybe already in bucket")
                return			
            
            """		

                        
    async def n1qlTimeSplit(self, qTime):
        d = {"m":0, "s":0, "ms":0}
        if len(qTime.split("ms")) > 1:
            d["ms"] = round(float(qTime[:-2]) ,1)

        if len(qTime.split("s")) > 1 and len(qTime.split("ms")) <= 1 :
            
            if "m" in qTime[:-1]:
                e = qTime[:-1]
                f = e.split("m")
                d["s"] = round(float(f[1]), 1)
            else:
                d["s"] = round(float(qTime[:-1]), 1)

        if len(qTime.split("m")) > 1 and len(qTime.split("ms")) <= 1 :

            if len(qTime[0]) > 0:
                d["m"] = round(float(qTime[0]), 2)
            else:
                d["m"] = round(float(qTime[:-1]), 2)
            
        return d

    async def replicateCheck(self, x):
        b = {}
        if "Replicate" in x:
            a = await self.replicatorId(x)
            if len(a) > 1 and a[0] == "DBG":
                t = await self.getTimeFromLine(x)
                since = await self.findSince(x)
                chkPt = await self.findCheckPts(x)
                #er = self.replicateError(x)
                id1 = self.sgLogTag+"::replicate::" + str(a[1]) + "::" + t[0]
                #check if in dictionary already
                if id1 in b: 
                    if since is not None:
                        b[id1]["since"] = since
                    if len(chkPt) > 0:
                        if chkPt[0] == 1:
                            b[id1]["getChk"] += 1
                        if chkPt[1] == 1:
                            b[id1]["setChk"] += 1
                else:
                    b.update({id1:{"repId":str(a[1]), "docType":"replicate", "since":since, "getChk":0, "setChk":0, "error":0, "dt":t[0], "tag":self.sgLogTag}})
        for y in b:
            await self.cbUpsert(y, b[y], self.cbTtl)

    async def replicatorId(self, line):
        return re.findall(r"\[([A-Za-z0-9_-]+)\]", line)

    async def findSince(self, line):
        pattern = r'Since:(\S+)'
        match = re.search(pattern, line)
        if match:
            return match.group(1)
        else:
            return ""
            
    async def findContinuous(self, line):
        continuous_str = None
        for substr in line.split():
            if substr.startswith('Continuous:'):
                continuous_str = substr.split(':')[1]
                break
        if continuous_str:
            if continuous_str.lower() == 'true':
                return True
            elif continuous_str.lower() == 'false':
                return False
        else:
            return None

    
    async def findChannelsList(self, line):
        channels = line.split('Channels:')[1].split(',')
        channels = [channel.split('/')[-1].strip() for channel in channels]
        return channels

    async def findCheckPts(self, line):
        a = []
        if "point" in line.lower():
            if "stateFnActivePushCheckpoint got event: {PUSH_CHECKPOINT_SUCCEEDED" in line:
                a = [0, 1]
            if "event: &{FETCH_CHECKPOINT_SUCCEEDED" in line:
                a = [1, 0]
        return a

    async def replicateError(self, line,replicatorName):
        if replicatorName in line.lower():
            ic(line)

    async def iso8601_to_epoch(self, timestamp):
        try:
            dt1 = datetime.datetime.fromisoformat(timestamp)
            return int(dt1.timestamp())
        except ValueError:
            pass
        
        try:
            dt2 = datetime.datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%fZ')
            seconds = time.mktime(dt2.timetuple()) + dt2.microsecond/1000000.0
            return int(seconds)
        except ValueError:
            pass

        return False
    
    async def cbInsert(self, key, doc,ttl=0):
        if "*" in self.debug or "cb" in self.debug:
            ic("CB Insert: Key:", key, "Doc:", doc)
            
        #opts = InsertOptions(timeout=timedelta(seconds=5))
        try:
            #r = self.cbColl.insert(key,doc,opts,expiry=timedelta(seconds=ttl))
            r = await self.cbColl.insert(key, doc, expiry=timedelta(seconds=ttl))
            if "*" in self.debug or "cb" in self.debug:
                ic(r)
            return r
        except CouchbaseException:
            ic(traceback.format_exc())
            ic("Error: Insert Key: ", key)
            return False
        
    async def cbUpsert(self, key, doc, ttl=0):
        #opts = InsertOptions(timeout=timedelta(seconds=5))
        if "*" in self.debug or "cb" in self.debug:
            ic("CB Upsert: Key:", key, "Doc:", doc)
        try:
            #r = self.cbColl.upsert(key,doc,opts,expiry=timedelta(seconds=ttl))
            r = await self.cbColl.upsert(key, doc, expiry=timedelta(seconds=ttl))
            if "*" in self.debug or "cb" in self.debug:
                ic(r)
            return r
        except CouchbaseException:
            ic(traceback.format_exc())
            ic("Error: Upsert Key: ", key)
            return False	
        
    async def cbGet(self, key):
        try:
            result = await self.cbColl.get(key)
            r = result.content_as[dict]
            if "*" in self.debug or "cb" in self.debug:
                ic("CB Get: Key:", key, "Result:", r)
            return r
        except DocumentNotFoundException:
            return False
        except CouchbaseException:
            ic(traceback.format_exc())
            ic("Error: Getting Key: ", key)
            return False
    
    async def cbSubDocAppend(self, key, value, data, ttl=0):
        if "*" in self.debug or "cb" in self.debug:
            ic("CB SubDoc Append: Key:", key, "Value:", value, "Data:", data)
        try:
            r = await self.cbColl.mutate_in(key, SD.upsert(value, data),)
            ic(r)
            return r
        except DocumentNotFoundException:
            return False
        except CouchbaseException:
            ic(traceback.format_exc())
            ic("Error: SubDoc Array Append for: ", key)
            return False
        
    async def cbSubDocInsert(self, key, value, data,ttl=0):
        if "*" in self.debug or "cb" in self.debug:
            ic("CB SubDoc Insert: Key:", key, "Value:", value, "Data:", data)
        try:
            r = await self.cbColl.mutate_in(key, SD.insert(value, data),)
            ic(r)
            return r
        except DocumentNotFoundException:
            return False
        except CouchbaseException:
            ic(traceback.format_exc())
            ic("Error: SubDoc Insert for: ", key)
            return False

    async def cbSubDocFind(self, key, value):	
        try:
            r = await self.cbColl.lookup_in(key, SD.get(value))
            if "*" in self.debug or "cb" in self.debug:
                ic("CB SubDoc Get: Key",key,"Value:",value,"Result:",r)
            return r
        except DocumentNotFoundException:
            return False
        except CouchbaseException:
            ic(traceback.format_exc())
            ic("Error: SubDoc Get for: ", key)
            return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        configFile = sys.argv[1]
    else:
        print("Error: No config.json file given")
        exit()

    a = work(configFile)
    del a

    '''
    with cProfile.Profile() as pr:
        work(configFile)

    stats = pstats.Stats(pr)
    stats.sort_stats(pstats.SortKey.TIME)
    stats.print_stats()
    stats.dump_stats(filename="test3.prof")
    '''


    '''
    def split_list(input_list, num_splits):
    avg = len(input_list) // num_splits
    out = []
    last = 0.0

    while last < len(input_list):
        out.append(input_list[int(last):int(last + avg)])
        last += avg

    return out


    # Create a list of numbers from 10000 to 17000
    numbers = list(range(10000, 17001))

    # Split the list into 4 smaller lists
    split_numbers = split_list(numbers, 4)

    # Print the smaller lists
    for i, small_list in enumerate(split_numbers):
        print(f"List {i+1}: {small_list}")
    
    
    
    '''
    
    ##bootstrap reads config.json and loads logfile into memory to read
    
    ##1.HTTP Logs

    ##2a.WS-ID-per-user-list      -- Completed
    #wsIdList = a.findWsId()    

    ##2b.from-WS-ID-diagnose-User -- Completed(but slow on big files)

    #a.getDataPerWsId(wsIdList) 
    ##3.SG-start times
    #a.sgStarts()
    ##4.DCP-errors-counter -- Completed
    #a.dcpChecks()

    ##5.n1ql-Query-times
    #a.sqlCheck()

    ##6.Golang-errors

    ##7.Imports -- Completed
    ##a.importCheck() -- Completed
    ##8. SG-Replicate
    #a.replicateCheck()