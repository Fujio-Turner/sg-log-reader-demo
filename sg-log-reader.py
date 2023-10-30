import sys
import json
from datetime import timedelta
from icecream import ic

import traceback

from couchbase.auth import PasswordAuthenticator
from couchbase.cluster import Cluster
import couchbase.subdocument as SD
from couchbase.options import (ClusterOptions, ClusterTimeoutOptions, QueryOptions)
from couchbase.exceptions import CouchbaseException
from couchbase.exceptions import DocumentNotFoundException

import re
import datetime , time
import uuid
import cProfile
import pstats


class work():

	debug = False
	cb = None
	sgLogName = "sg_debug.log"
	cbHost = "127.0.0.1"
	cbUser = "Administrator"
	cbPass = "fujiofujio"
	cbBucketName = "sg-log-reader"
	cbScopeName = "_default"
	cbCollectionName = "_default"
	cbColl = None
	logData = None
	wsIdList = {}
	wasBlipLines = False
	blipLineCount = 0
	oldWsDic = {}
	sgDtLineOffset = 0
	sgLogTag = "default"
	logLineDepthLevel = 1000
	logLineDepthPercent = 0.02
	logNumberOflines = 1



	def __init__(self,file):
		self.readConfigFile(file)
		self.debugIceCream()
		self.makeCB()
		self.openSgLogFile()

	def makeCB(self):
		try:
			auth = PasswordAuthenticator(self.cbUser, self.cbPass)
			cluster = Cluster('couchbase://'+self.cbHost, ClusterOptions(auth))
			cluster.wait_until_ready(timedelta(seconds=5))

			self.cb = cluster.bucket(self.cbBucketName)
			#self.cbColl = self.cb.scope(self.cbScopeName).collection(self.cbCollectionName)
			self.cbColl = self.cb.default_collection()
		except:
			ic("Error: Could not connect to CB Cluster: " , self.cbHost ," as: ",self.cbUser )
			exit()

	def diffdates(self,d1, d2):
		return (time.mktime(time.strptime(d2,"%Y-%m-%dT%H:%M:%S")) - time.mktime(time.strptime(d1, "%Y-%m-%dT%H:%M:%S")))

	def debugIceCream(self):
		if self.debug == True:
			ic.enable();
		else:
			ic.disable()

	def readConfigFile(self,configFile):
		a = open(configFile, "rb" )
		b = json.loads(a.read())
		self.sgLogName = b["file-to-parse"]
		self.cbHost = b["cb-cluster-host"]
		self.cbBucket = b["cb-bucket-name"]
		self.cbUser = b["cb-bucket-user"]
		self.cbPass = b["cb-bucket-user-password"]
		self.debug = b["debug"]
		self.sgDtLineOffset = b["dt-log-line-offset"]
		self.sgLogTag = b["log-name"]
		a.close()

	def openSgLogFile(self):
		bigOne = []
		index = 0	
		print("Starting - Reading Data File: ",datetime.datetime.now())
		with open(self.sgLogName, "r") as a:
			b = [line.strip() for line in a.readlines()]
		counter = 1
		for x in b:
			counter +=1
			ic(x)
			line = x.rstrip('\r|\n')
			bigOne.append(line)
			#self.importCheck(line)
			#self.n1qlQueryInfo(line)
			#self.replicateCheck(line)
			#self.dcpChecks(line)
			#self.sgStarts(line)
			if self.wasBlipLines == True:
				ic(line)
				self.findWsId(line,index)

			self.findBlipLine(line,index)
			index +=1
		self.logNumberOflines = counter
		self.logLineDepthLevel = counter * self.logLineDepthPercent
		print("Number - Lines in log file: ",counter)
		print("Number - WebSocket Connections: ",self.blipLineCount)
		print("Done - Reading Data File: ",datetime.datetime.now())
		self.logData = bigOne
		ic(self.wsIdList)
		self.getDataPerWsId()
		if self.debug == True:
			ic(self.logData)

	def findBlipLine(self,x,lineNumb):
		if "/_blipsync" in x: 
			self.blipLineCount += 1
			userN = self.getUserName(x)
			t = self.getTimeFromLine(x)
			httpNum = self.httpTransNum(x)
			k = httpNum+userN[1]
			self.wsIdList[k] = {"user":userN[1],"sgDb":userN[0],"auth":False,"dt":t[0],"dtFullEpoch":self.iso8601_to_epoch(t[1]),"http":httpNum}
			self.wasBlipLines = True

	def findWsId(self,wsLine,index):
		if "Upgraded to BLIP+WebSocket protocol" in wsLine or "Upgraded to WebSocket" in wsLine:
			c = re.findall(r"\[([A-Za-z0-9_]+)\]", wsLine)
			if len(c) > 1:
				#check if ws in new or old
				userN = self.getUserNameBlip(wsLine)
				
				httpNum = self.httpTransNumPlus(wsLine)

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

	def httpTransNumPlus(self,line):
		h = line.split(" HTTP+: ")
		return h[1].split(" ")[0]

	def httpTransNum(self,line):
		h = line.split(" HTTP:  ")
		return h[1].split(" ")[0]

	def getUserName(self,line):

		c = line.split(" ")
		#c = re.findall(r"\(([A-Za-z0-9_]+)\)", line)
		sgDb = c[6].split("/")[1]
		usrN = c[-1].rstrip(')')

		if "<ud>" in line and "</ud>" in line:
			pattern = r'\(as <ud>(.*?)</ud>\)'
			# Use re.search to find the first match for the pattern in the log line
			match = re.search(pattern, line)
			# If a match is found, print the matched string
			if match:
				return [sgDb,match.group(1)]
		else:
			return [sgDb,usrN]

	def getUserNameBlip(self,line):
		#c = re.findall(r"\(([A-Za-z0-9_]+)\)", line)

		if "<ud>" in line and "</ud>" in line:
			pattern = r'\(as <ud>(.*?)</ud>\)'
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

	def getDataPerWsId(self):
		print("Starting - Per wsId : ",datetime.datetime.now())
		#sinceList = []
		ic(self.wsIdList)
		for key, x in self.wsIdList.items():
			z = self.getDataPerWsIdWorker(x)
			if self.debug == True:
				ic(x,z)
			else:
				try:
					self.cbColl.upsert(z[0],z[1])
				except CouchbaseException:
					ic(traceback.format_exc())
					ic("Error: Update of Key: ",x)

		print("Done - Per wsId : ",datetime.datetime.now())

	def getDataPerWsIdWorker(self,x):
		sinceList = []

		
		if x["auth"] == True:
			w = x["ws"]

			r = self.loopLog(x["ws"],x["startLine"],sinceList)
			tf = self.getTimeFromLine(r[0][0])
			tl = self.getTimeFromLine(r[0][-1])

			if r[1] != None:
				sinceList.append(r[1])
			tRow = 0
			if r[2] != None:
				tRow = r[2]
			if r[3] != None:
				tRow = tRow + r[3]
			if tf[0] != None and tl[0] != None:
				df = self.diffdates(tf[0],tl[0])
			else:
				df = None
			d = {
				"docType":"byWsId",
				"user":x["user"],
				"dtFullEpoch":self.iso8601_to_epoch(tf[1]),
				"dt":tf[0],
				"dtEnd":tl[0],
				"dtDiffSec":df,
				"sgDb":x["sgDb"],
				"since":sinceList,
				"continuous":r[8],
				"conflicts":r[9],
				"errors":r[10],
				"warnings":r[11],
				"cRow":r[2],
				"qRow":r[3],
				"tRow":tRow,
				"sentCount":r[12],
				"attSuccess": r[13],
				"filterBy":r[5],
				"logTag":self.sgLogTag,
				"blipC":r[6],
				"blipO":r[7],
				"auth":True,
				"cbTicket":"",
				"log":r[0]
				}
		else:
			w = str(uuid.uuid1())
			d = {
			"docType":"byWsId",
			"user":x["user"],
			"sgDb":x["sgDb"],
			"dtFullEpoch":x['dtFullEpoch'],
			"dt":x['dt'],
			"auth":False,
			"cbTicket":"",
			"logTag":self.sgLogTag,
			}

		return [w,d]

	
					
	def loopLog(self,wsId,startLogLine,sinceList):
		logLine = []
		channelRow = 0
		queryRow = 	0
		conflictCount = 0
		errorCount = 0
		warningCount = 0
		sent = 0
		goErrors = 0
		dcpErrors = 0
		importErrors = 0
		attTotal = 0
		attSuc = 0
		attFail = 0
		since = None
		filterBy = False
		blipClosed = False
		blipOpened = False
		filterByChannels = []
		continuous = None

		passIt = 0
		for x in self.logData[startLogLine:]:

			if wsId in x and "WS" not in x:
				if blipClosed == False:
					passIt = 0
				cleanLine = x.rstrip('\r|\n')
				logLine.append(cleanLine)
				if "Since:" in x and "SyncMsg:" in x:
					if "Since:0 " in x: #looks for _change since=0
						since = "0"
					else:
						since = self.findSince(x)

				if "GetCachedChanges(\"" in x:
					c = self.changeCacheCount(x)
					channelRow = channelRow + c
					continue
				if "GetChangesInChannel(" in x:
					d = self.changeQueryCount(x)					
					queryRow = queryRow + d
					continue
				if " Continuous:" in x and " SyncMsg:" in x:
					continuous = self.findContinuous(x)
					continue
				if "BLIP+WebSocket connection closed" in x:
					passIt = self.logLineDepthLevel - 50
					blipClosed = True
					continue
				if "Upgraded to BLIP+WebSocket protocol" in x:
					blipOpened = True
					continue
				if "Filter:sync_gateway/bychannel" in x:
					filterBy = True
					filterByChannels = self.findChannelsList(x)
					continue
				if " changes to client, from seq " in x:		
					j = self.findSentCount(x)
					sent = sent + j
					continue
				if " proveAttachment successful for doc " in x:		
					attSuc = attSuc + 1
					continue
				if " 409 Document update conflict " in x:
					conflictCount = conflictCount + 1
					continue
				if "[ERR] c:[" in x:
					errorCount += 1
					continue
				if "[WRN] c:[" in x:
					warningCount += 1
					continue
				if "Type:proposeChanges" in x:
					proChange = 1
					continue
			else:
				passIt += 1
			if passIt >= self.logLineDepthLevel:
				return [logLine,since,channelRow,queryRow,filterBy,filterByChannels,blipClosed,blipOpened,continuous,conflictCount,errorCount,warningCount,sent,attSuc]
				
		return [logLine,since,channelRow,queryRow,filterBy,filterByChannels,blipClosed,blipOpened,continuous,conflictCount,errorCount,warningCount,sent,attSuc]

	def changeCacheCount(self,line):
		a = line.split(" ")
		if self.debug == True:
			ic(a)

		if a[7] == "got":
			return int(a[8])
		else:
			return int(a[7])

	def changeQueryCount(self,line):
		a = line.split(" ")
		if self.debug == True:
			ic(a)
		return int(a[6])

	def getTimeFromLine(self,line):
		return [line[0+self.sgDtLineOffset:19+self.sgDtLineOffset].rstrip("-"),line[0+self.sgDtLineOffset:24+self.sgDtLineOffset].rstrip("-")]

	def sgStarts(self,x):
		if "==== Couchbase Sync Gateway/" in x:
			t = self.getTimeFromLine(x)
			d = {"docType":"sgStart","dt":t[0],"tag":self.sgLogTag}
			try:
				self.cbColl.upsert(self.sgLogTag+"::sgStart::"+t[0],d)
			except CouchbaseException:
				ic(traceback.format_exc())
				ic("Error: Update of Key: ",self.sgLogTag+"::sgStart::"+t[0])

	def dcpChecks(self,x):
		if "DCP: OnError:" in x:
			t = self.getTimeFromLine(x)
			d = {"docType":"dcpError","dt":t[0] ,"count":1,"tag":self.sgLogTag}

			try:
				self.cbColl.mutate_in(self.sgLogTag+"::dcpErorr::"+t[0], SD.upsert("count",d["count"]+1))
			except DocumentNotFoundException:
				r = self.cbColl.insert(self.sgLogTag+"::query::"+t[0],d)
				ic(r)
			except CouchbaseException:
				ic(traceback.format_exc())
				ic("Error: Inserting Key: ","sgStart::"+t," maybe already in bucket")
				self.cbColl.insert(self.sgLogTag+"::dcpErorr::"+t[0],d)

	def importCheck(self,x):
		if " Import" in x:
			t = self.getTimeFromLine(x)
			if "error during importDoc" in x:
				ic(t[0],x)
				return

	def findSentCount(self,x):
		a = x.split(" ")
		if self.debug == True:
			ic(a)
		return int(a[5])

	def n1qlQueryInfo(self,x):

		if "Query: N1QL Query" in x:

			t = self.getTimeFromLine(x)
			a = x.split(" ")
			b = self.n1qlTimeSplit(a[6])
			c = {"q":a[4],"t":a[6],"dt":t[0],"tChop":b,"tag":self.sgLogTag}
			d = {"docType":"query", "q":[c]}

			ic(b)
			try:
				t = self.cbColl.mutate_in(self.sgLogTag+"::query::"+t[0], (SD.array_append('q',b),))
			except DocumentNotFoundException:
				r = self.cbColl.insert(self.sgLogTag+"::query::"+t[0],d)
				ic(r)
			except CouchbaseException:
				ic(traceback.format_exc())
				ic("Error: Inserting Key: ","sgStart::"+t," maybe already in bucket")


		if "Channel query" in x:

			t = self.getTimeFromLine(x)
			a = x.split(" ")			
			b = self.n1qlTimeSplit(a[5])
			c = {"q":a[3],"t":int(a[8]),"chan":a[12],"dt":t[0],"st":a[14],"end":a[16],"tChop":b,"tag":self.sgLogTag}
			d = {"docType":"query", "q":[c]}
			
			try:
				t = self.cbColl.mutate_in(self.sgLogTag+"::query::"+t[0], (SD.array_append('q',b),))
			except DocumentNotFoundException:
					r = self.cbColl.insert(self.sgLogTag+"::query::"+t[0],d)
					ic(r)
			except CouchbaseException:
				ic(traceback.format_exc())
				ic("Error: Inserting Key: ","sgStart::"+t," maybe already in bucket")
						
	def n1qlTimeSplit(self,qTime):
		d = {"m":0,"s":0,"ms":0}
		if len(qTime.split("ms")) > 1:
			d["ms"] = round(float(qTime[:-2]),1)

		if len(qTime.split("s")) > 1 and len(qTime.split("ms")) <= 1 :
			
			if "m" in qTime[:-1]:
				e = qTime[:-1]
				f = e.split("m")
				d["s"] = round(float(f[1]),1)
			else:
				d["s"] = round(float(qTime[:-1]),1)

		if len(qTime.split("m")) > 1 and len(qTime.split("ms")) <= 1 :

			if len(qTime[0]) > 0:
				d["m"] = round(float(qTime[0]),2)
			else:
				d["m"] = round(float(qTime[:-1]),2)
			
		return d

	def replicateCheck(self,x):
		b = {}
		if "Replicate" in x:
			a = self.replicatorId(x)
			if len(a) > 1 and a[0] == "DBG":
				t = self.getTimeFromLine(x)
				since = self.findSince(x)
				chkPt = self.findCheckPts(x)
				#er = self.replicateError(x)
				id1 = self.sgLogTag+"::replicate::" + str(a[1]) +"::"+ t[0]
				#check if in dictionary already
				if id1 in b: 
					if since != None:
						b[id1]["since"] = since
					if len(chkPt) > 0:
						if chkPt[0] == 1:
							b[id1]["getChk"] += 1
						if chkPt[1] == 1:
							b[id1]["setChk"] += 1
				else:
					b.update({id1:{"repId":str(a[1]),"docType":"replicate","since":since,"getChk":0,"setChk":0,"error":0,"dt":t[0],"tag":self.sgLogTag}})
		for y in b:
			try:
				self.cbColl.upsert(y,b[y])
			except CouchbaseException:
				ic(traceback.format_exc())
				ic("Error: Upsert Key:",y)

	def replicatorId(self,line):
		return re.findall(r"\[([A-Za-z0-9_-]+)\]",line)


	def findSince(self,line):
		pattern = r'Since:(\S+)'
		match = re.search(pattern, line)
		if match:
			return match.group(1)
		else:
			return ""
			
	def findContinuous(self,line):
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

	
	def findChannelsList(self,line):
		channels = line.split('Channels:')[1].split(',')
		channels =[channel.split('/')[-1].strip() for channel in channels]
		return channels

	def findCheckPts(self,line):
		a = []
		if "point" in line.lower():
			if "stateFnActivePushCheckpoint got event: {PUSH_CHECKPOINT_SUCCEEDED" in line:
				a = [0,1]
			if "event: &{FETCH_CHECKPOINT_SUCCEEDED" in line:
				a = [1,0]
		return a

	def replicateError(self,line,replicatorName):
		if replicatorName in line.lower():
			ic(line)

	def iso8601_to_epoch(self,timestamp):

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
		


if __name__ == "__main__":
	if len(sys.argv) > 1:
		configFile = sys.argv[1]
	else:
		print("Error: No config.json file given")
		exit()
	a = work(configFile)
	

	'''
	with cProfile.Profile() as pr:
		work(configFile)

	stats = pstats.Stats(pr)
	stats.sort_stats(pstats.SortKey.TIME)
	stats.print_stats()
	stats.dump_stats(filename="test3.prof")
	'''
	
	##bootstrap reads config.json and loads logfile into memory to read
	


	##1.HTTP Logs

	##2a.WS-ID-per-user-list
	#wsIdList = a.findWsId()

	##2b.from-WS-ID-diagnose-User
	#a.getDataPerWsId(wsIdList)

	##3.SG-start times
	#a.sgStarts()
	##4.DCP-errors-counter
	#a.dcpChecks()

	##5.n1ql-Query-times
	#a.n1qlQueryInfo()

	##6.Golang-errors

	##7.Imports
	##a.importCheck()
	##8. SG-Replicate
	#a.replicateCheck()