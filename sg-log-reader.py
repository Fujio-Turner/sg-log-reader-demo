#!/usr/bin/python
import sys
import re
import json
import datetime
from datetime import datetime

class SGLOGREADER():

	file = ''
	debug = False
	dotimes = False
	dotrans = True
	sgRestart = {"r":False}
	masterConfig = {}
	tempTransData = {}
	timesSGlog = {}

	def __init__(self,file):
		self.file = file
	
	def processLog(self):

		file = open(self.file,"r")

		self.masterConfig.update({"parsedFileName":self.file})
		self.masterConfig.update({"timeScriptRan":str(datetime.now())})

		onLine = 1 		 		
		for line in file:

			if self.debug == True:
				print "line: " + str(onLine) 

			processedTimeStamp = self.processTimeStamp(line,onLine)
			#print processedTimeStamp
			if processedTimeStamp == False:
				continue
			if " HTTP:" in line:
			 processedHttp = self.processHTTP(line,processedTimeStamp["min"],processedTimeStamp["sec"],processedTimeStamp["mil"])
			if " HTTP+:" in line:
			 processedHttp = self.processHTTPplus(line,processedTimeStamp["min"],processedTimeStamp["sec"],processedTimeStamp["mil"])
			onLine += 1

		file.close()

		if self.dotrans == True:
			self.masterConfig.update({"trans":self.tempTransData})
		#print json.dumps(self.tempTransData)
		if self.debug == False:
			print json.dumps(self.masterConfig)
		
	def processHTTP(self,line='',lineTimeMin='',lineTimeMax='',lineTimeMil=''):

		## TYPE
		httpType = "Other"
		if "POST" in line:
			self.processPost(line,lineTimeMin,lineTimeMax,lineTimeMil)
			httpType = "POST"
		elif "GET" in line:
			httpType = "GET"
			self.processGet(line,lineTimeMin,lineTimeMax,lineTimeMil)
		elif "PUT" in line:
			self.processPut(line,lineTimeMin,lineTimeMax,lineTimeMil)
			httpType = "PUT"
		elif "DELETE" in line:
			self.processDelete(line,lineTimeMin,lineTimeMax,lineTimeMil)
			httpType = "DELETE"
		else:
			self.processHTTPother(line,'other',lineTimeMin,lineTimeMax,lineTimeMil)
			httpType = "other"


		#self.processTransTimes(line,'request',lineTimeMin,lineTimeMax)

		'''
		#url Split
		url = re.findall(r'\?(.*)',line)
		y = ''
		for x in url:
			y = x
		z = y.split(" ")
		print z[0]
		'''
	def processHTTPother(self,line = '',dType = 'other',lineTime='',lineTimeSec='',lineTimeMil=''):

		'''
		if "HTTP" in self.masterConfig:
			if "OTHER" in self.masterConfig["HTTP"]:
				if dType in self.masterConfig["HTTP"]["OTHER"]:
					if "times" in self.masterConfig["HTTP"]["OTHER"][dType]:
						if lineTime in self.masterConfig["HTTP"]["OTHER"][dType]["times"]:
							self.masterConfig["HTTP"]["OTHER"][dType]["times"][lineTime]["num"] += 1
							if "times" in self.masterConfig["HTTP"]["OTHER"][dType]["times"][lineTime]:
								if lineTimeSec in self.masterConfig["HTTP"]["OTHER"][dType]["times"][lineTime]["times"]:
									self.masterConfig["HTTP"]["OTHER"][dType]["times"][lineTime]["times"][lineTimeSec]["num"] += 1
								else:
									self.masterConfig["HTTP"]["OTHER"][dType]["times"][lineTime]["times"].update({lineTimeSec:{"num":1}})
							else:
								self.masterConfig["HTTP"]["OTHER"][dType]["times"][lineTime].update({"times":{lineTimeSec:{"num":1}}})
						else:
							self.masterConfig["HTTP"]["OTHER"][dType]["times"].update({lineTime:{"num":1,"times":{lineTimeSec:{"num":1}}}})
					else:
						self.masterConfig["HTTP"]["OTHER"][dType].update({"times":{lineTime:{"num":1,"times":{lineTimeSec:{"num":1}}}}})
				else:
					self.masterConfig["HTTP"]["OTHER"].update({dType:{"times":{lineTime:{"num":1,"times":{lineTimeSec:{"num":1}}}}}})
			else:
				self.masterConfig["HTTP"].update({"OTHER":{dType:{"times":{lineTime:{"num":1,"times":{lineTimeSec:{"num":1}}}}}}})
		else:
			self.masterConfig.update({"HTTP":{"OTHER":{dType:{"times":{lineTime:{"num":1,"times":{lineTimeSec:{"num":1}}}}}}}})
		'''
		self.processTransTimes(line,"OTHER",dType,"response",lineTime,lineTimeSec,lineTimeMil)
		return True

	def processHTTPplus(self,line = '',lineTime='',lineTimeMax='',lineTimeMil=''):
		response = line.split(" --> ")
		responseType = 'unknown'
		responseTime = re.findall('\(.*?\)$',response[1]) #start at the end of the line.
		cleanedResponseTime = responseTime[0].replace("(","").replace(")","").split(" ")
	
		#trans = re.findall(r'#\d+',line)
			#if self.debug == True:
			#print str(trans[0]) + " :"+lineTime+' :End'

		self.processTransTimes(line,"","","response",lineTime,lineTimeMax,lineTimeMil)


	def processChanges(self,line='',dType='',lineTime='',lineTimeSec='',lineTimeMil=''):

		if self.debug == True:
			print "_changes"

		if "HTTP" in self.masterConfig:
			if dType in self.masterConfig["HTTP"]:
				if '_changes' in self.masterConfig["HTTP"][dType]:
					if "times" in self.masterConfig["HTTP"][dType]["_changes"]:
						if lineTime in self.masterConfig["HTTP"][dType]["_changes"]["times"]:
							self.masterConfig["HTTP"][dType]["_changes"]["times"][lineTime]["num"] += 1
							if "times" in self.masterConfig["HTTP"][dType]["_changes"]["times"][lineTime]:
								if lineTimeSec in self.masterConfig["HTTP"][dType]["_changes"]["times"][lineTime]["times"]:
									self.masterConfig["HTTP"][dType]["_changes"]["times"][lineTime]["times"][lineTimeSec]["num"] += 1
								else:
									self.masterConfig["HTTP"][dType]["_changes"]["times"][lineTime]["times"].update({lineTimeSec:{"num":1}})
							else:
								self.masterConfig["HTTP"][dType]["_changes"]["times"][lineTime].update({"times":{lineTimeSec:{"num":1}}})
						else:
							self.masterConfig["HTTP"][dType]["_changes"]["times"].update({lineTime:{"num":1,"times":{lineTimeSec:{"num":1}}}})
					else:
						self.masterConfig["HTTP"][dType]["_changes"].update({"times":{lineTime:{"num":1,"times":{lineTimeSec:{"num":1}}}}})
				else:
					self.masterConfig["HTTP"][dType].update({"_changes":{"times":{lineTime:{"num":1,"times":{lineTimeSec:{"num":1}}}}}})
			else:
				self.masterConfig["HTTP"].update({dType:{"_changes":{"times":{lineTime:{"num":1,"times":{lineTimeSec:{"num":1}}}}}}})
		else:
			self.masterConfig.update({"HTTP":{dType:{"_changes":{"times":{lineTime:{"num":1,"times":{lineTimeSec:{"num":1}}}}}}}})	
		
		self.processTransTimes(line,dType,"_changes","request",lineTime,lineTimeSec,lineTimeMil)
		return True

	def processGet(self,line='',lineTime='',lineTimeSec='',lineTimeMil=''):

		dType = '/'

		if  "/_local/" in line:
			dType = '_local'
		elif "/_role" in line:
			dType ="ADMIN:_role"
		elif "/_config" in line:
			dType ="ADMIN:_config"
		elif "/_raw" in line:
			dType ="ADMIN:_raw"
		elif "/_user" in line:
			dType ="ADMIN:_user"
		elif "/_user/" in line:
			dType ="ADMIN:_user(all)"
		elif "/_session/" in line:
			dType ="_session"
		elif "/_oidc" in line:
			dType ="AUTH:_oidc"
		elif "/_oidc_callback" in line:
			dType ="AUTH:_oidc_callback"
		elif "/_oidc_challenge" in line:
			dType ="AUTH:_oidc_challenge"
		elif "/_oidc_refresh" in line:
			dType ="AUTH:_oidc_refresh"

		if dType == "/_changes":
			if self.debug == True:
				print "_changes"
			self.processChanges(line,"GET",lineTime,lineTimeSec,lineTimeMil)
			return True

		if self.debug == True:
			print "GET: " + dType

		if "HTTP" in self.masterConfig:
			if "GET" in self.masterConfig["HTTP"]:
				if dType in self.masterConfig["HTTP"]["GET"]:
					if "times" in self.masterConfig["HTTP"]["GET"][dType]:
						if lineTime in self.masterConfig["HTTP"]["GET"][dType]["times"]:
							self.masterConfig["HTTP"]["GET"][dType]["times"][lineTime]["num"] += 1
							if "times" in self.masterConfig["HTTP"]["GET"][dType]["times"][lineTime]:
								if lineTimeSec in self.masterConfig["HTTP"]["GET"][dType]["times"][lineTime]["times"]:
									self.masterConfig["HTTP"]["GET"][dType]["times"][lineTime]["times"][lineTimeSec]["num"] += 1
								else:
									self.masterConfig["HTTP"]["GET"][dType]["times"][lineTime]["times"].update({lineTimeSec:{"num":1}})
							else:
								self.masterConfig["HTTP"]["GET"][dType]["times"][lineTime].update({"times":{lineTimeSec:{"num":1}}})
						else:
							self.masterConfig["HTTP"]["GET"][dType]["times"].update({lineTime:{"num":1,"times":{lineTimeSec:{"num":1}}}})
					else:
						self.masterConfig["HTTP"]["GET"][dType].update({"times":{lineTime:{"num":1,"times":{lineTimeSec:{"num":1}}}}})
				else:
					self.masterConfig["HTTP"]["GET"].update({dType:{"times":{lineTime:{"num":1,"times":{lineTimeSec:{"num":1}}}}}})
			else:
				self.masterConfig["HTTP"].update({"GET":{dType:{"times":{lineTime:{"num":1,"times":{lineTimeSec:{"num":1}}}}}}})
		else:
			self.masterConfig.update({"HTTP":{"GET":{dType:{"times":{lineTime:{"num":1,"times":{lineTimeSec:{"num":1}}}}}}}})
		
		self.processTransTimes(line,"GET",dType,"request",lineTime,lineTimeSec,lineTimeMil)
		return True

	def processPut(self,line='',lineTime='',lineTimeSec='',lineTimeMil=''):

		dType = '/'
		
		if  "/_local/" in line:
			dType = "_local"
		if  "/_bulk_get" in line:
			dType = "_bulk_get"
		elif "/_logging" in line:
			dType = '_all_docs'
		elif "/_design/" in line:
			dType ="ADMIN:_role"
		elif "/_role/" in line:
			dType ="ADMIN:_role"
		elif "/_config" in line:
			dType ="ADMIN:_config"
		elif "/_user/" in line:
			dType ="ADMIN:_user"

		if "HTTP" in self.masterConfig:
			if "PUT" in self.masterConfig["HTTP"]:
				if dType in self.masterConfig["HTTP"]["PUT"]:
					if "times" in self.masterConfig["HTTP"]["PUT"][dType]:
						if lineTime in self.masterConfig["HTTP"]["PUT"][dType]["times"]:
							self.masterConfig["HTTP"]["PUT"][dType]["times"][lineTime]["num"] += 1
							if "times" in self.masterConfig["HTTP"]["PUT"][dType]["times"][lineTime]:
								if lineTimeSec in self.masterConfig["HTTP"]["PUT"][dType]["times"][lineTime]["times"]:
									self.masterConfig["HTTP"]["PUT"][dType]["times"][lineTime]["times"][lineTimeSec]["num"] += 1
								else:
									self.masterConfig["HTTP"]["PUT"][dType]["times"][lineTime]["times"].update({lineTimeSec:{"num":1}})
							else:
								self.masterConfig["HTTP"]["PUT"][dType]["times"][lineTime].update({"times":{lineTimeSec:{"num":1}}})
						else:
							self.masterConfig["HTTP"]["PUT"][dType]["times"].update({lineTime:{"num":1,"times":{lineTimeSec:{"num":1}}}})
					else:
						self.masterConfig["HTTP"]["PUT"][dType].update({"times":{lineTime:{"num":1,"times":{lineTimeSec:{"num":1}}}}})
				else:
					self.masterConfig["HTTP"]["PUT"].update({dType:{"times":{lineTime:{"num":1,"times":{lineTimeSec:{"num":1}}}}}})
			else:
				self.masterConfig["HTTP"].update({"PUT":{dType:{"times":{lineTime:{"num":1,"times":{lineTimeSec:{"num":1}}}}}}})
		else:
			self.masterConfig.update({"HTTP":{"PUT":{dType:{"times":{lineTime:{"num":1,"times":{lineTimeSec:{"num":1}}}}}}}})
		
		self.processTransTimes(line,"PUT",dType,"request",lineTime,lineTimeSec,lineTimeMil)
		return True	

	def processPost(self,line='',lineTime='',lineTimeSec='',lineTimeMil=''):

		dType = '/'

		if "/_bulk_docs" in line:
			dType ="_bulk_docs"
		elif "/_bulk_get" in line:
			dType ="_bulk_get"
		elif "/_all_docs" in line:
			dType ="_all_docs"
		elif "/_changes" in line:
			dType ="_changes"
		elif "/_compact" in line:
			dType ="ADMIN:_compact"
		elif "/_offline" in line:
			dType ="ADMIN:_offline"
		elif "/_online" in line:
			dType ="ADMIN:_online"
		elif "/_resync" in line:
			dType ="ADMIN:_resync"		
		elif "/_role" in line:
			dType ="ADMIN:_role"
		elif "/_logging" in line:
			dType ="ADMIN:_logging"
		elif "/_replicate" in line:
			dType ="ADMIN:_replicate"
		elif "/_purge" in line:
			dType ="ADMIN:_purge"
		elif "/_config" in line:
			dType ="ADMIN:_config"
		elif "/_raw" in line:
			dType ="ADMIN:_raw"
		elif "/_revs_diff" in line:
			dType ="_revs_diff"
		elif "/_user" in line:
			dType ="ADMIN:_user"
		elif "/_session" in line:
			dType ="ADMIN:_session"

		#processing _changes
		if dType == "_changes":
			if self.debug == True:
					print "_changes"
			self.processChanges(line,"POST",lineTime,lineTimeSec,lineTimeMil)
			return True

		if "HTTP" in self.masterConfig:
			if "POST" in self.masterConfig["HTTP"]:
				if dType in self.masterConfig["HTTP"]["POST"]:
					if "times" in self.masterConfig["HTTP"]["POST"][dType]:
						if lineTime in self.masterConfig["HTTP"]["POST"][dType]["times"]:
							self.masterConfig["HTTP"]["POST"][dType]["times"][lineTime]["num"] += 1
							if "times" in self.masterConfig["HTTP"]["POST"][dType]["times"][lineTime]:
								if lineTimeSec in self.masterConfig["HTTP"]["POST"][dType]["times"][lineTime]["times"]:
									self.masterConfig["HTTP"]["POST"][dType]["times"][lineTime]["times"][lineTimeSec]["num"] += 1
								else:
									self.masterConfig["HTTP"]["POST"][dType]["times"][lineTime]["times"].update({lineTimeSec:{"num":1}})
							else:
								self.masterConfig["HTTP"]["POST"][dType]["times"][lineTime].update({"times":{lineTimeSec:{"num":1}}})
						else:
							self.masterConfig["HTTP"]["POST"][dType]["times"].update({lineTime:{"num":1,"times":{lineTimeSec:{"num":1}}}})
					else:
						self.masterConfig["HTTP"]["POST"][dType].update({"times":{lineTime:{"num":1,"times":{lineTimeSec:{"num":1}}}}})
				else:
					self.masterConfig["HTTP"]["POST"].update({dType:{"times":{lineTime:{"num":1,"times":{lineTimeSec:{"num":1}}}}}})
			else:
				self.masterConfig["HTTP"].update({"POST":{dType:{"times":{lineTime:{"num":1,"times":{lineTimeSec:{"num":1}}}}}}})
		else:
			self.masterConfig.update({"HTTP":{"POST":{dType:{"times":{lineTime:{"num":1,"times":{lineTimeSec:{"num":1}}}}}}}})
		
		self.processTransTimes(line,"POST",dType,"request",lineTime,lineTimeSec,lineTimeMil)
		return True	

	def processDelete(self,line='',lineTime='',lineTimeSec='',lineTimeMil=''):

			dType = '/'

			if "/_local/" in line:
				dType ="_local"
			elif "/_role/" in line:
				dType ="ADMIN:_role"
			elif "/_design/" in line:
				dType ="ADMIN:_design"
			elif "/_user/" in line:
				dType ="ADMIN:_user"
			elif "/_session/" in line:
				dType ="ADMIN:_session"
			
			
			if "HTTP" in self.masterConfig:
				if "DELETE" in self.masterConfig["HTTP"]:
					if dType in self.masterConfig["HTTP"]["DELETE"]:
						if "times" in self.masterConfig["HTTP"]["DELETE"][dType]:
							if lineTime in self.masterConfig["HTTP"]["DELETE"][dType]["times"]:
								self.masterConfig["HTTP"]["DELETE"][dType]["times"][lineTime]["num"] += 1
								if "times" in self.masterConfig["HTTP"]["DELETE"][dType]["times"][lineTime]:
									if lineTimeSec in self.masterConfig["HTTP"]["DELETE"][dType]["times"][lineTime]["times"]:
										self.masterConfig["HTTP"]["DELETE"][dType]["times"][lineTime]["times"][lineTimeSec]["num"] += 1
									else:
										self.masterConfig["HTTP"]["DELETE"][dType]["times"][lineTime]["times"].update({lineTimeSec:{"num":1}})
								else:
									self.masterConfig["HTTP"]["DELETE"][dType]["times"][lineTime].update({"times":{lineTimeSec:{"num":1}}})
							else:
								self.masterConfig["HTTP"]["DELETE"][dType]["times"].update({lineTime:{"num":1,"times":{lineTimeSec:{"num":1}}}})
						else:
							self.masterConfig["HTTP"]["DELETE"][dType].update({"times":{lineTime:{"num":1,"times":{lineTimeSec:{"num":1}}}}})
					else:
						self.masterConfig["HTTP"]["DELETE"].update({dType:{"times":{lineTime:{"num":1,"times":{lineTimeSec:{"num":1}}}}}})
				else:
					self.masterConfig["HTTP"].update({"DELETE":{dType:{"times":{lineTime:{"num":1,"times":{lineTimeSec:{"num":1}}}}}}})
			else:
				self.masterConfig.update({"HTTP":{"DELETE":{dType:{"times":{lineTime:{"num":1,"times":{lineTimeSec:{"num":1}}}}}}}})
			

			self.processTransTimes(line,"DELETE",dType,"request",lineTime,lineTimeSec,lineTimeMil)
			return True	


	def processTransTimes(self,line='',rType = 'POST',rValue = '_changes',dataAsk = 'request',lineTimeMin='',lineTimeMax='',lineTimeMil=''):

			trans = re.findall(r'#\d+',line)

			if len(trans) == 0:
				return False

			#print dataAsk 

			#check if they started SG and Trans went back to #001

			prePendTrans = 0
			firstTime = False

			if self.sgRestart["r"] == False and dataAsk == "request" and trans[0] == "#001":
				firstTime = True
				trans[0] = str(1) + str(trans[0])
				self.sgRestart.update({"r":1})

			if self.sgRestart["r"] == False and dataAsk == "response" and trans[0] == "#001":

				firstTime = True
				trans[0] = str(1) + str(trans[0])
				self.sgRestart.update({"r":1})

			if self.sgRestart["r"] != False and trans[0] == "#001" and firstTime == False and self.sgRestart["r"] >= 1 and dataAsk =="request":
				prePendTrans = str(self.sgRestart["r"] + 1)
				trans[0] = prePendTrans + str(trans[0])
				self.sgRestart["r"] +=1


			if trans[0] != "#001" and firstTime == False:
				trans[0] = str(self.sgRestart["r"])+ str(trans[0])

			if self.sgRestart["r"] != False and trans[0] == "#001" and self.sgRestart["r"] >= 1 and dataAsk =="response":
				trans[0] = str(self.sgRestart["r"]) + str(trans[0])

			if self.debug == True:
				if dataAsk == 'request':
					print str(trans[0])  + " :"+lineTimeMil+' :Start'
				else:
					print str(trans[0])  + " :"+lineTimeMil+' :End'


			if trans[0] in self.tempTransData:				
				if dataAsk == 'response':
					
					self.tempTransData[trans[0]].update({"e":lineTimeMil})
					
					if self.tempTransData[trans[0]]["s"] != "":
						
						if self.tempTransData[trans[0]]["s"] == lineTimeMil:
							self.tempTransData[trans[0]].update({"d":"0:00:00.000000"})
						else:
							#print self.tempTransData[trans[0]]["s"] +" - " + lineTimeMil
							d1 = datetime.strptime(self.tempTransData[trans[0]]["s"],"%Y-%m-%d %H:%M:%S.%f")
							d2 = datetime.strptime(lineTimeMil,"%Y-%m-%d %H:%M:%S.%f")
							d3 = str(d2 - d1)[:-3]
							#print str(d3/1000)
							self.tempTransData[trans[0]].update({"d":d3})
							if 'd' in self.masterConfig["HTTP"][self.tempTransData[trans[0]]["t"]][self.tempTransData[trans[0]]["v"]]["times"][self.tempTransData[trans[0]]["sec"][:-3]]["times"][self.tempTransData[trans[0]]["sec"]]:
								#have to compare the highest one and replace if bigger
								if self.masterConfig["HTTP"][self.tempTransData[trans[0]]["t"]][self.tempTransData[trans[0]]["v"]]["times"][self.tempTransData[trans[0]]["sec"][:-3]]["times"][self.tempTransData[trans[0]]["sec"]]["d"] < d3:
									self.masterConfig["HTTP"][self.tempTransData[trans[0]]["t"]][self.tempTransData[trans[0]]["v"]]["times"][self.tempTransData[trans[0]]["sec"][:-3]]["times"][self.tempTransData[trans[0]]["sec"]]["d"] = d3
							else:	
								self.masterConfig["HTTP"][self.tempTransData[trans[0]]["t"]][self.tempTransData[trans[0]]["v"]]["times"][self.tempTransData[trans[0]]["sec"][:-3]]["times"][self.tempTransData[trans[0]]["sec"]].update({"d":d3})
				else:
					self.tempTransData[trans[0]].update({"s":lineTimeMil})
			else:
				self.tempTransData.update({trans[0]:{"t":rType,"v":rValue,"sec":lineTimeMax,"s":lineTimeMil,"e":""}}) #add in trans
				#self.tempTransData.update({lineTimeMax:{trans[0]:{"t":rType,"v":rValue,"l":lineTimeMil,"h":lineTimeMil}}}) #add in trans
			return True

	def processTimeStamp(self,line='',linePosition = 0):
			timestamplong = str(line[:23])
			
			if len(timestamplong) <= 1:
				return False
			#print "show :"+ str(len(timestamp)) + ":end"
			#exit()
			if timestamplong[10] == "T":
				timestamplong = re.sub("T", " ", timestamplong)
			timestamp =	timestamplong[:19]
			timestampMinute = timestamp[:16]
			#per minutel/second
			if self.dotimes == True:	
				if 'times' in self.masterConfig:
					if timestampMinute in self.masterConfig["times"]:
						self.masterConfig["times"][timestampMinute]["num"] += 1
						if "times" in self.masterConfig["times"][timestampMinute]:
							if timestamp in self.masterConfig["times"][timestampMinute]["times"]:
								self.masterConfig["times"][timestampMinute]["times"][timestamp]["num"] += 1
							else:
								self.masterConfig["times"][timestampMinute]["times"].update({timestamp:{"num":1,"line":linePosition}})
						else:
							self.masterConfig["times"][timestampMinute]["times"].update({timestamp:{"num":1,"line":linePosition}})
					else:
						self.masterConfig["times"].update({timestampMinute:{"num":1,"line":linePosition,"times":{timestamp:{"num":1,"line":linePosition}}}})
				else:
					self.masterConfig.update({"times":{timestampMinute:{"num":1,"line":linePosition,"times":{timestamp:{"num":1,"line":linePosition}}}}})
			return {"min":timestampMinute,"sec":timestamp,"mil":timestamplong}

	def checkSGrestart(self,lineParsed=0):
		print 'yes'

if __name__ == "__main__":
	
	path = sys.argv[1]
	a = SGLOGREADER(path)
	a.processLog()
