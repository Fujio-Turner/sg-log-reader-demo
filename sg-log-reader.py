#!/usr/bin/python
import sys
sys.path.insert(0, r'/usr/local/lib/python2.7/site-packages/')

import json
from couchbase.cluster import Cluster
from couchbase.cluster import PasswordAuthenticator
import couchbase.subdocument as SD
import re


class work():

	debug = False
	cb = None
	sgLogName = "sg_debug.log"
	cbHost = "127.0.0.1"
	cbUser = "Administrator"
	cbPass = "password"
	cbBucket = "bucket"
	logData = None
	wsIdList = []
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
		for x in a:
			bigOne.append(x.rstrip('\r|\n'))
		a.close()
		self.logData = bigOne
		if self.debug == True:
			print(self.logData)

	def findWsId(self):
		ws = []
		index = 0
		for x in self.logData:
			if "/_blip" in x: 
				#get name of user
				userN = self.getUserName(x)
				#get WSnumber
				c = re.findall(r"\[([A-Za-z0-9_]+)\]", self.logData[index+1])
				if len(c) > 1:
					#print(c[1])
					ws.append({"ws":c[1],"usr":userN[1],"sgDb":userN[0],"startLine":index+1})
			index +=1
		self.wsIdList = ws
		return self.wsIdList


	def getUserName(self,line):
		c = line.split(" ")
		#c = re.findall(r"\(([A-Za-z0-9_]+)\)", line)
		sgDb = c[6].split("/")[1]
		usrN = c[-1].rstrip(')')
		return [sgDb,usrN]

	def getDataPerWsId(self,wsList):
		for x in wsList:
			r = self.loopLog(x["ws"],x["startLine"])
			dt = r[0][0].split(" ")
			tRow = 0
			if r[2] != None:
				tRow = r[2]
			if r[3] != None:
				tRow = tRow + r[3]

			d = {
				"type":"byWsId",
				"usr":x["usr"],
				"log":r[0],
				"dt":dt[0],
				"sgDb":x["sgDb"],
				"sin":r[1],
				"cRow":r[2],
				"qRow":r[3],
				"tRow":tRow,
				"tag":self.sgLogTag
				}

			if self.debug == True:
				print(x["ws"],d)
			else:
				self.cb.upsert(x["ws"],d)

	def loopLog(self,wsId,startLogLine):
		a = []
		channelRow = 0
		queryRow = 	0
		since = None
		#for x in self.logData:
		for x in self.logData[startLogLine:]:
			if wsId in x and "WS" not in x:
				#b = x.rstrip('\r|\n').replace("{","").replace("}","").replace("\\","").replace('"',"").replace('/',"").decode("utf8")
				b = x.rstrip('\r|\n').decode("utf8")
				a.append(b)
				if "Since:0" in x: #looks for _change since=0
					since = "0"
				if "GetCachedChanges(\"" in x:
					c = self.changeCacheCount(x)
					channelRow = channelRow + c
				if "GetChangesInChannel(" in x:
					d = self.changeQueryCount(x)
					queryRow = queryRow + d
		if queryRow == 0:
			queryRow = None
		return [a,since,channelRow,queryRow]

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

	def getTimeForLineBySecond(self,line):
		return line[0+self.sgDtLineOffset:19+self.sgDtLineOffset]


	def sgStarts(self):
		for x in self.logData:
			if "==== Couchbase Sync Gateway/" in x:
				t = self.getTimeForLineBySecond(x)
				d = {"type":"sgStart","dt":t,"tag":self.sgLogTag}
				try:
					self.cb.insert("sgStart::"+t,d)
				except:
					print("Error: Inserting Key: ","sgStart::"+t," maybe already in bucket")

	def dcpChecks(self):

		for x in self.logData:
			if "DCP: OnError:" in x:
				t = self.getTimeForLineBySecond(x)
				d = {"type":"dcpError","dt":t ,"count":1,"tag":self.sgLogTag}

				try:
					d = self.cb.get("dcpErorr::"+t).value
					self.cb.mutate_in("dcpErorr::"+t, SD.upsert("count",d["count"]+1))
				except:
					#print("Error: Inserting Key: ","sgStart::"+t," maybe already in bucket")
					self.cb.insert("dcpErorr::"+t,d)

	def importCheck(self):
		return

	def n1qlQueryInfo(self):
		for x in self.logData:
			if "Query: N1QL Query" in x:
				t = self.getTimeForLineBySecond(x)

				a = x.split(" ")
				b = self.n1qlTimeSplit(a[6])
				c = {"q":a[4],"t":a[6],"dt":a[0],"tChop":b,"tag":self.sgLogTag}
				d = {"type":"query", "q":[c]}
				try:
					#d = self.cb.get("query::"+t).value
					self.cb.mutate_in("query::"+t, SD.array_append('q',b))
				except:
					#print("Error: Inserting Key: ","sgStart::"+t," maybe already in bucket")
					self.cb.insert("query::"+t,d)

	def n1qlTimeSplit(self,qTime):

		d = {"m":0,"s":0,"ms":0}
		if len(qTime.split("ms")) > 1:
			d["ms"] = round(float(qTime[:-2]),1)
		if len(qTime.split("s")) > 1 and len(qTime.split("ms")) <= 1 :
			d["s"] = round(float(qTime[:-1]),1)
		if len(qTime.split("m")) > 1 and len(qTime.split("ms")) <= 1 :
			d["m"] = round(float(qTime[:-1]),2)
		return d



if __name__ == "__main__":

	if len(sys.argv) > 1:
		configFile = sys.argv[1]
	else:
		print("Error: No config.json file given")
		exit()

	a = work(configFile) ##bootstrap reads config.json and loads logfile into memory to read
	
	##1.HTTP Logs

	##2a.WS-ID-per-user-into-cb
	wsIdList = a.findWsId()
	##2b.from-WS-ID-diagnose-User
	c = a.getDataPerWsId(wsIdList)
	##3.SG-start/restarts-counts
	a.sgStarts()
	
	##4.DCP-errors-from-CB
	a.dcpChecks()

	##5.Query-times
	a.n1qlQueryInfo()

	##6.Golang-errors

	##7.Imports
	a.importCheck()

	##8. SG-Replicate

