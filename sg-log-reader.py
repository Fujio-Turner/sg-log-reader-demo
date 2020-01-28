#!/usr/bin/python
import sys
sys.path.insert(0, r'/usr/local/lib/python2.7/site-packages/')

import json
from couchbase.cluster import Cluster
from couchbase.cluster import PasswordAuthenticator
import couchbase.subdocument as SD
import re
import datetime
import time 
import uuid

class work():

	debug = False
	cb = None
	sgLogName = "sg_debug.log"
	cbHost = "127.0.0.1"
	cbUser = "Administrator"
	cbPass = "password"
	cbBucket = "bucket"
	logData = None
	wsIdList = {}
	wasBlipLines = False
	oldWsDic = {}
	sgDtLineOffset = 0
	sgLogTag = "default"
	
	def __init__(self,file):
		self.readConfigFile(file)
		self.makeCB()
		self.openSgLogFile()

	def makeCB(self):
		cluster = Cluster('couchbase://'+self.cbHost)
		authenticator = PasswordAuthenticator(self.cbUser, self.cbPass)
		cluster.authenticate(authenticator)
		try:
			self.cb = cluster.open_bucket(self.cbBucket)
		except:
			print("Error: Could not connect to CB Cluster: " , self.cbHost ," as: ",self.cbUser )
			exit()

	def diffdates(self,d1, d2):
		return (time.mktime(time.strptime(d2,"%Y-%m-%dT%H:%M:%S")) - time.mktime(time.strptime(d1, "%Y-%m-%dT%H:%M:%S")))

	def readConfigFile(self,configFile):
		a = open(configFile, "rb" )
		
		if self.debug == True:
			print(a.read())

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
		a = open(self.sgLogName, "r")
		index = 0
		for x in a:
			line = x.rstrip('\r|\n').decode("utf8")
			bigOne.append(line)
			self.importCheck(line)
			self.n1qlQueryInfo(line)
			self.replicateCheck(line)
			self.dcpChecks(line)
			self.sgStarts(line)
			if self.wasBlipLines == True:
				#print(line)
				self.findWsId(line,index)

			self.findBlipLine(line,index)
			index +=1
		a.close()
		#print(self.wsIdList)
		self.logData = bigOne
		self.getDataPerWsId()
		if self.debug == True:
			print(self.logData)

	def findBlipLine(self,x,lineNumb):
		if "/_blip" in x: 
			userN = self.getUserName(x)
			t = self.getTimeFromLine(x)
			httpNum = self.httpTransNum(x)
			k = httpNum+userN[1]
			self.wsIdList[k] = {"user":userN[1],"sgDb":userN[0],"auth":False,"dt":t[0],"http":httpNum}
			self.wasBlipLines = True

	def findWsId(self,wsLine,index):
		if "Upgraded to BLIP+WebSocket protocol" in wsLine:
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
		return [sgDb,usrN]

	def getUserNameBlip(self,line):
		#c = re.findall(r"\(([A-Za-z0-9_]+)\)", line)
		c = line.split(" ")
		if c[15] != "":
			d = c[15].rstrip('.')
			return d.split(":")[1]
		if c[16] != "":
			return c[16].rstrip(')')

	def getDataPerWsId(self):
		sinceList = []
		#print(wsList)
		for key, x in self.wsIdList.items():
		#for x in self.wsIdList:
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
					"type":"byWsId",
					"user":x["user"],
					"dt":tf[0],
					"dtEnd":tl[0],
					"dtDiffSec":df,
					"sgDb":x["sgDb"],
					"since":sinceList,
					"cRow":r[2],
					"qRow":r[3],
					"tRow":tRow,
					"filterBy":r[4],
					"logTag":self.sgLogTag,
					"blipC":r[5],
					"blipO":r[6],
					"auth":True,
					"log":r[0]
					}
			else:
				w = str(uuid.uuid1())
				d = {
				"type":"byWsId",
				"user":x["user"],
				"sgDb":x["sgDb"],
				"dt":x["dt"],
				"auth":False,
				"logTag":self.sgLogTag,
				}

			sinceList = []
			if self.debug == True:
				print(x,d)
			else:
				self.cb.upsert(w,d)

	def loopLog(self,wsId,startLogLine,sinceList):
		a = []
		channelRow = 0
		queryRow = 	0
		since = None
		filterBy = False
		blipClosed = False
		blipOpened = False
		filterByChannels = []
		#for x in self.logData:
		for x in self.logData[startLogLine:]:
			if wsId in x and "WS" not in x:
				#b = x.rstrip('\r|\n').replace("{","").replace("}","").replace("\\","").replace('"',"").replace('/',"").decode("utf8")
				b = x.rstrip('\r|\n')
				a.append(b)

				if "Since:" in x:
					if "Since:0 " in x: #looks for _change since=0
						since = "0"
					else:
						sinceLong = x.split("Since:")[1]
						since = sinceLong.split(" ")[0]
				if "GetCachedChanges(\"" in x:
					c = self.changeCacheCount(x)
					channelRow = channelRow + c
				if "GetChangesInChannel(" in x:
					d = self.changeQueryCount(x)
					queryRow = queryRow + d

				if "BLIP+WebSocket connection closed" in x:
					blipClosed = True
				if "Upgraded to BLIP+WebSocket protocol" in x:
					blipOpened = True

		##if queryRow == 0:
		##	queryRow = None
		return [a,since,channelRow,queryRow,filterBy,blipClosed,blipOpened]

	def changeCacheCount(self,line):
		a = line.split(" ")
		if self.debug == True:
			print(a)

		if a[7] == "got":
			return int(a[8])
		else:
			return int(a[7])

	def changeQueryCount(self,line):
		a = line.split(" ")
		if self.debug == True:
			print(a)
		return int(a[6])

	def getTimeFromLine(self,line):
		return [line[0+self.sgDtLineOffset:19+self.sgDtLineOffset],line[0+self.sgDtLineOffset:24+self.sgDtLineOffset]]

	def sgStarts(self,x):
		if "==== Couchbase Sync Gateway/" in x:
			t = self.getTimeFromLine(x)
			d = {"type":"sgStart","dt":t[0],"tag":self.sgLogTag}
			try:
				self.cb.upsert(self.sgLogTag+"::sgStart::"+t[0],d)
			except:
				print("Error: Update of Key: ",self.sgLogTag+"::sgStart::"+t[0])

	def dcpChecks(self,x):
		if "DCP: OnError:" in x:
			t = self.getTimeFromLine(x)
			d = {"type":"dcpError","dt":t[0] ,"count":1,"tag":self.sgLogTag}

			try:
				d = self.cb.get(self.sgLogTag+"::dcpErorr::"+t[0]).value
				self.cb.mutate_in(self.sgLogTag+"::dcpErorr::"+t[0], SD.upsert("count",d["count"]+1))
			except:
				#print("Error: Inserting Key: ","sgStart::"+t," maybe already in bucket")
				self.cb.insert(self.sgLogTag+"::dcpErorr::"+t[0],d)

	def importCheck(self,x):
		if " Import" in x:
			t = self.getTimeFromLine(x)
			if "error during importDoc" in x:
				#print(t[0],x)
				return

	def n1qlQueryInfo(self,x):
		if "Query: N1QL Query" in x:
			t = self.getTimeFromLine(x)
			a = x.split(" ")
			b = self.n1qlTimeSplit(a[6])
			c = {"q":a[4],"t":a[6],"dt":t[0],"tChop":b,"tag":self.sgLogTag}
			d = {"type":"query", "q":[c]}
			try:
				#d = self.cb.get("query::"+t).value
				self.cb.mutate_in(self.sgLogTag+"::query::"+t[0], SD.array_append('q',b))
			except:
				#print("Error: Inserting Key: ","sgStart::"+t," maybe already in bucket")
				self.cb.insert(self.sgLogTag+"::query::"+t[0],d)

	def n1qlTimeSplit(self,qTime):
		d = {"m":0,"s":0,"ms":0}
		if len(qTime.split("ms")) > 1:
			d["ms"] = round(float(qTime[:-2]),1)
		if len(qTime.split("s")) > 1 and len(qTime.split("ms")) <= 1 :
			d["s"] = round(float(qTime[:-1]),1)
		if len(qTime.split("m")) > 1 and len(qTime.split("ms")) <= 1 :
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
					b.update({id1:{"repId":str(a[1]),"type":"replicate","since":since,"getChk":0,"setChk":0,"error":0,"dt":t[0],"tag":self.sgLogTag}})
		for y in b:
			try:
				self.cb.upsert(y,b[y])
			except:
				print("Error: Upsert Key:",y)

	def replicatorId(self,line):
		return re.findall(r"\[([A-Za-z0-9_-]+)\]",line)


	def findSince(self,line):
		if "since" in line:
			b = line.split("&since=")
			#c = re.findall(r"\since=([0-9_:]+)\&", line)
			if len(b) > 1:
				return b[1].split("&")[0]
			else:
				return None

	def findCheckPts(self,line):
		a = []
		if "point" in line.lower():
			#[getCheckpoints,setCheckpoint]
			if "stateFnActivePushCheckpoint got event: {PUSH_CHECKPOINT_SUCCEEDED" in line:
				a = [0,1]
			if "event: &{FETCH_CHECKPOINT_SUCCEEDED" in line:
				a = [1,0]
		return a

	def replicateError(self,line,replicatorName):
		if replicatorName in line.lower():
			print(line)

if __name__ == "__main__":

	if len(sys.argv) > 1:
		configFile = sys.argv[1]
	else:
		print("Error: No config.json file given")
		exit()

	a = work(configFile) ##bootstrap reads config.json and loads logfile into memory to read
	
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

