from datetime import timedelta
from icecream import ic

import traceback

from couchbase.auth import PasswordAuthenticator
from couchbase.cluster import Cluster
import couchbase.subdocument as SD
from couchbase.options import (ClusterOptions, ClusterTimeoutOptions, QueryOptions)
from couchbase.exceptions import CouchbaseException
from couchbase.exceptions import DocumentNotFoundException


from flask import Flask,render_template,request

class work():

	debug = False
	cb = None
	sgLogName = "sg_debug.log"
	cbHost = "127.0.0.1"
	cbUser = "Administrator"
	cbPass = "fujiofujio"
	cbBucketName = "sg-log-reader"
	cluster = None
	cbScopeName = "_default"
	cbCollectionName = "_default"
	cbColl = None
	logData = None
	wsIdList = {}
	wasBlipLines = False
	oldWsDic = {}
	sgDtLineOffset = 0
	sgLogTag = "default"

	def __init__(self):
		self.debugIceCream()
		self.makeCB()

	def makeCB(self):
		try:
			auth = PasswordAuthenticator(self.cbUser, self.cbPass)
			self.cluster = Cluster('couchbase://'+self.cbHost, ClusterOptions(auth))
			self.cluster.wait_until_ready(timedelta(seconds=5))

			self.cb = self.cluster.bucket(self.cbBucketName)
			#self.cbColl = self.cb.scope(self.cbScopeName).collection(self.cbCollectionName)
			self.cbColl = self.cb.default_collection()
		except:
			ic("Error: Could not connect to CB Cluster: " , self.cbHost ," as: ",self.cbUser )
			exit()


	def debugIceCream(self):
		if self.debug == True:
			ic.enable();
		else:
			ic.disable()
			
	def cbWsIdGet(self,wsId):
		ic(wsId)
		try:
			return self.cbColl.get(wsId['wsId']).value
		except DocumentNotFoundException:
			ic("wsId doc not found for: ",wsId)
			return {}
		except CouchbaseException:
			ic(traceback.format_exc())
			return {}
		
	def cbSgDbNameList(self,rangeData):
		ic(rangeData)
		if 'startDt' not in rangeData or not rangeData["startDt"] or 'endDt' not in rangeData or not rangeData["endDt"]:
			return []

		q = 'SELECT  count(u.`sgDb`) as `sgDbCount` , u.`sgDb` FROM `'+self.cbBucketName+'`.`'+self.cbScopeName +'`.`'+ self.cbCollectionName+'` as u WHERE u.`docType` = "byWsId"'
		q = q + ' AND u.dt BETWEEN $startDt AND $endDt ' 
		q = q + ' AND u.`sgDb` IS NOT MISSING '
		q = q + ' AND u.`user` IS NOT MISSING '
		q = q + ' AND u.`orphane` = False '
		q = q + ' GROUP BY u.`sgDb` '
		q = q + ' ORDER BY u.`sgDb` '

		data = []
		try:
			result = self.cluster.query(q, QueryOptions(named_parameters=rangeData))
			for row in result.rows():
				data.append(row)
			return data
		except CouchbaseException:
			ic(traceback.format_exc())
			return []

	def cbDtRangeSearch(self,rangeData):

		ic(rangeData)
		if 'sgDb' not in rangeData or not rangeData["sgDb"]:
			return []
		
		q = 'SELECT ' 
		if rangeData["viewBy"] and rangeData["viewBy"] == "sec":
		
			q = q + ' u.`dt`, COUNT(u.`dt`) as `dtCount` , SUM(u.`dtDiffSec`) as `dtDiffSec`,  SUM(u.`cRow`) as `cRow` , SUM(u.`qRow`) as `qRow`, SUM(u.`tRow`) as `tRow`, SUM(u.`conflicts`) as `conflicts`, SUM(u.`errors`) as `errors` , SUM(u.`sentCount`) as `sentCount`, SUM(u.`pushAttCount`) as `pushAttCount`, SUM(u.`pushCount`) as `pushCount`, SUM(u.`pullAttCount`) as `pullAttCount` ' 
		
		elif rangeData["viewBy"] and rangeData["viewBy"] == "min" :
		
			q = q + ' SUBSTR(u.`dt`,1,15) as `dt`, COUNT(SUBSTR(u.`dt`,1,15)) as `dtCount`, SUM(u.`dtDiffSec`) as `dtDiffSec`,  SUM(u.`cRow`) as `cRow` , SUM(u.`qRow`) as `qRow`, SUM(u.`tRow`) as `tRow`, SUM(u.`conflicts`) as `conflicts`, SUM(u.`errors`) as `errors` , SUM(u.`sentCount`) as `sentCount`, SUM(u.`pushAttCount`) as `pushAttCount`, SUM(u.`pushCount`) as `pushCount`, SUM(u.`pullAttCount`) as `pullAttCount` ' 

		else:
			q = q + ' u.`dt`,u.`user`,meta(u).id as cbKey, u.`dtDiffSec`, u.`cRow`,u.`qRow`,u.`tRow`,u.`conflicts`,u.`errors` , u.`sentCount`, u.`blipC`,u.`since`, u.`pushAttCount`, u.`pushCount`,u.`pullAttCount` ' 

		q = q + ' FROM `'+self.cbBucketName+'`.`'+self.cbScopeName +'`.`'+ self.cbCollectionName+'` as u WHERE u.`docType` = "byWsId"'
		q = q + ' AND u.dt BETWEEN $startDt AND $endDt ' 
		q = q + ' AND u.`sgDb` = $sgDb '
		q = q + ' AND u.`user` IS NOT MISSING '
		q = q + ' AND u.`orphane` = False '

		if rangeData["noPushes"] and rangeData["noPushes"] == "no":
			q = q + ' AND u.`pushCount` = 0 '

		if rangeData["noPushes"] and rangeData["noPushes"] == "only":
			q = q + ' AND u.`pushCount` > 0 '

		if rangeData["syncResult"] and rangeData["syncResult"] == "full":
			q = q + ' AND u.`sentCount` = u.`tRow` '

		if rangeData["syncResult"] and rangeData["syncResult"] == "nonFull":
			q = q + ' AND u.`sentCount` != u.`tRow` '

		if rangeData["syncResult"] and rangeData["syncResult"] == "no":
				q = q + ' AND u.`sentCount` = 0 '

		if rangeData["errors"] and rangeData["errors"] == True:
			q = q + ' AND u.`errors` > 0 '

		if rangeData["conflicts"] and rangeData["conflicts"] == True:
			q = q + ' AND u.`conflicts` > 0 '
		
		if rangeData["sinceZero"] and rangeData["sinceZero"] == True:
			q = q + ' AND u.`since` = ["0"] '

		if rangeData["filterByChannels"] and rangeData["filterByChannels"] == True:
			q = q + ' AND ARRAY_LENGTH(u.`filterBy`) > 0 '

		if rangeData["attachments"] and rangeData["attachments"] == True:
			q = q + ' AND u.`pushAttCount` > 0 '

		if rangeData["attachmentsPull"] and rangeData["attachmentsPull"] == True:
			q = q + ' AND u.`pullAttCount` > 0 '

		if rangeData["syncTime"]:
			q = q + ' AND u.`dtDiffSec` >= TONUMBER('+rangeData["syncTime"]+') '

		if rangeData["changeCount"] :
			q = q + ' AND u.`tRow` >= TONUMBER('+rangeData["changeCount"]+') '

		if 'user' not in rangeData or not rangeData["user"]:
			q = q + ' AND u.`user` IS NOT MISSING '
		else:
			q = q + ' AND u.`user` = $user '

		if rangeData["viewBy"] and rangeData["viewBy"] == "sec":
			q = q + ' GROUP BY u.`dt` '

		if rangeData["viewBy"] and rangeData["viewBy"] == "min":
			q = q + ' GROUP BY SUBSTR(u.`dt`,1,15) '
			q = q + ' ORDER BY SUBSTR(u.`dt`,1,15) ASC '
		else:
			q = q + ' ORDER BY u.`dt` ASC '


		data = []
		ic(q)
		try:
			result = self.cluster.query(q, QueryOptions(named_parameters=rangeData))
			for row in result.rows():
				data.append(row)
			return data
		except CouchbaseException:
			ic(traceback.format_exc())
			return []
		
	def cbDtDiffStats(self,rangeData):

			ic(rangeData)
			if 'sgDb' not in rangeData or not rangeData["sgDb"]:
				return []
			
			q = 'SELECT COUNT(t.tRange) as tCount, tRange FROM ('
			q = q + ' SELECT CASE WHEN u.dtDiffSec <=1 then "01. 1 Sec or less" '
			q = q + ' WHEN u.dtDiffSec between 2 and 10 then "02. 2 to 10 Sec" '
			q = q + ' WHEN u.dtDiffSec between 11 and 30 then "03. 11 to 30 Sec" '
			q = q + ' WHEN u.dtDiffSec between 31 and 60 then "04. 31 to 60 Sec" '
			q = q + ' WHEN u.dtDiffSec between 61 and 120 then "05. 1 to 2 minutes" '
			q = q + ' WHEN u.dtDiffSec between 121 and 300 then "06. 2 to 5 minutes" '
			q = q + ' WHEN u.dtDiffSec between 301 and 900 then "07. 5 to 15 minutes" '
			q = q + ' WHEN u.dtDiffSec between 901 and 1800 then "08. 15 to 30 minutes" '
			q = q + ' WHEN u.dtDiffSec between 1801 and 3600 then "09. 30 to 60 minutes" '
			q = q + ' WHEN u.dtDiffSec > 3601 then "10. 60 minutes or more"' 
			q = q + ' else "11. n/a" '
			q = q + ' END  as tRange '
			q = q + ' FROM `'+self.cbBucketName+'`.`'+self.cbScopeName +'`.`'+ self.cbCollectionName+'` as u WHERE u.`docType` = "byWsId" '
			q = q + ' AND u.dt BETWEEN $startDt AND $endDt ' 
			q = q + ' AND u.`sgDb` = $sgDb '
			q = q + ' AND u.`orphane` = False '

			if rangeData["noPushes"] and rangeData["noPushes"] == "no":
				q = q + ' AND u.`pushCount` = 0 '

			if rangeData["noPushes"] and rangeData["noPushes"] == "only":
				q = q + ' AND u.`pushCount` > 0 '

			if rangeData["syncResult"] and rangeData["syncResult"] == "full":
				q = q + ' AND u.`sentCount` = u.`tRow` '

			if rangeData["syncResult"] and rangeData["syncResult"] == "nonFull":
				q = q + ' AND u.`sentCount` != u.`tRow` '

			if rangeData["syncResult"] and rangeData["syncResult"] == "no":
				q = q + ' AND u.`sentCount` = 0 '

			if rangeData["errors"] and rangeData["errors"] == True:
				q = q + ' AND u.`errors` > 0 '

			if rangeData["conflicts"] and rangeData["conflicts"] == True:
				q = q + ' AND u.`conflicts` > 0 '
			
			if rangeData["sinceZero"] and rangeData["sinceZero"] == True:
				q = q + ' AND u.`since` = ["0"] '

			if rangeData["filterByChannels"] and rangeData["filterByChannels"] == True:
				q = q + ' AND ARRAY_LENGTH(u.`filterBy`) > 0 '

			if rangeData["attachments"] and rangeData["attachments"] == True:
				q = q + ' AND u.`pushAttCount` > 0 '

			if rangeData["attachmentsPull"] and rangeData["attachmentsPull"] == True:
				q = q + ' AND u.`pullAttCount` > 0 '

			if rangeData["syncTime"]:
				q = q + ' AND u.`dtDiffSec` >= TONUMBER('+rangeData["syncTime"]+') '

			if rangeData["changeCount"] :
				q = q + ' AND u.`tRow` >= TONUMBER('+rangeData["changeCount"]+') '

			if 'user' not in rangeData or not rangeData["user"]:
				q = q + ' AND u.`user` IS NOT MISSING '
			else:
				q = q + ' AND u.`user` = $user '

			q = q + ' ) as t GROUP BY t.tRange ORDER by t.tRange '
			data = []
			ic(q)

			try:
				result = self.cluster.query(q, QueryOptions(named_parameters=rangeData))
				for row in result.rows():
					data.append(row)
				return data
			except CouchbaseException:
				ic(traceback.format_exc())
				return []


	def cbUserSearch(self,userName):
		try:
			return self.cbColl.get(wsId).value
		except DocumentNotFoundException:
			ic("wsId doc not found for: ",wsId)
			return {}
		except CouchbaseException:
			ic(traceback.format_exc())
			return {}

	def cbUserList(self,rangeData):
		ic(rangeData)
		if 'startDt' not in rangeData or not rangeData["startDt"] or 'endDt' not in rangeData or not rangeData["endDt"] or 'sgDb' not in rangeData or not rangeData["sgDb"]:
			return []

		q = 'SELECT  count(u.`user`) as `sgUserCount` , u.`user` FROM `'+self.cbBucketName+'`.`'+self.cbScopeName +'`.`'+ self.cbCollectionName+'` as u WHERE u.`docType` = "byWsId"'
		q = q + ' AND u.dt BETWEEN $startDt AND $endDt ' 
		q = q + ' AND u.`sgDb` = $sgDb '
		q = q + ' AND u.`user` IS NOT MISSING '
		q = q + ' AND u.`orphane` = False '

		if rangeData["noPushes"] and rangeData["noPushes"] == "no":
			q = q + ' AND u.`pushCount` = 0 '

		if rangeData["noPushes"] and rangeData["noPushes"] == "only":
			q = q + ' AND u.`pushCount` > 0 '
	
		if rangeData["syncResult"] and rangeData["syncResult"] == "full":
			q = q + ' AND u.`sentCount` = u.`tRow` '

		if rangeData["syncResult"] and rangeData["syncResult"] == "nonFull":
			q = q + ' AND u.`sentCount` != u.`tRow` '

		if rangeData["syncResult"] and rangeData["syncResult"] == "no":
				q = q + ' AND u.`sentCount` = 0 '

		if rangeData["errors"] and rangeData["errors"] == True:
			q = q + ' AND u.`errors` > 0 '

		if rangeData["conflicts"] and rangeData["conflicts"] == True:
			q = q + ' AND u.`conflicts` > 0 '
		
		if rangeData["sinceZero"] and rangeData["sinceZero"] == True:
			q = q + ' AND u.`since` = ["0"] '

		if rangeData["filterByChannels"] and rangeData["filterByChannels"] == True:
			q = q + ' AND ARRAY_LENGTH(u.`filterBy`) > 0 '

		if rangeData["attachments"] and rangeData["attachments"] == True:
			q = q + ' AND u.`pushAttCount` > 0 '

		if rangeData["attachmentsPull"] and rangeData["attachmentsPull"] == True:
			q = q + ' AND u.`pullAttCount` > 0 '

		if rangeData["syncTime"]:
			q = q + ' AND u.`dtDiffSec` >= TONUMBER('+rangeData["syncTime"]+') '

		if rangeData["changeCount"] :
			q = q + ' AND u.`tRow` >= TONUMBER('+rangeData["changeCount"]+') '

		q = q + ' GROUP BY u.`user` '

		if 'sortBy' not in rangeData or not rangeData["sortBy"] or rangeData["sortBy"] == "name": 
			q = q + ' ORDER BY u.`user` '
		elif rangeData["sortBy"] == "count":
			q = q + ' ORDER BY `sgUserCount` DESC '

		ic(q)
		data = []
		try:
			result = self.cluster.query(q, QueryOptions(named_parameters=rangeData))
			for row in result.rows():
				data.append(row)
			ic(data)
			return data
		except CouchbaseException:
			ic(traceback.format_exc())
			return []

	def cbSgDbList(self,rangeDate):
		return {}
	def cbLastWsId(self):
		return {}
	
	def lastWs(self):

		q = 'SELECT  u.`dt` , META(u).id as cbKey FROM `'+self.cbBucketName+'`.`'+self.cbScopeName +'`.`'+ self.cbCollectionName+'` as u WHERE u.`docType` = "byWsId"'
		q = q + ' AND u.dt IS NOT MISSING '
		q = q + ' AND u.`sgDb` IS NOT MISSING '
		q = q + ' AND u.`user` IS NOT MISSING '
		q = q + ' AND u.`dtDiffSec` IS NOT MISSING '
		q = q + ' AND u.`orphane` = False '
		q = q + ' ORDER BY u.`dt` DESC '
		q = q + ' LIMIT 1'

		ic(q)
		data = []
		try:
			result = self.cluster.query(q)
			for row in result.rows():
				data.append(row)
			return data
		except CouchbaseException:
			ic(traceback.format_exc())
			return []


cb = work()

app = Flask(__name__)

@app.route('/')
def hello():
    return render_template('index.html')

@app.route('/dateRange', methods=['POST'])
def dateRange():
	if request.method == 'POST':
		ic(request.json)
		a = cb.cbDtRangeSearch(request.json)
		return a
	else:
		return []
	
@app.route('/dtDiffSecStats', methods=['POST'])
def dateDiffSec():
	if request.method == 'POST':
		ic(request.json)
		a = cb.cbDtDiffStats(request.json)
		return a
	else:
		return []


@app.route('/wsId',methods=['POST'])
def getWsId():
	if request.method == 'POST':
		ic(request.json)
		a = cb.cbWsIdGet(request.json)
		return a
	else:
		return []

@app.route('/sgDbList', methods=['POST'])
def sgDblist():
	if request.method == 'POST':
		ic(request.json)
		a = cb.cbSgDbNameList(request.json)
		return a
	else:
		return []

@app.route('/sgUserList',methods=['POST'])
def sgUserlist():
	if request.method == 'POST':
		ic(request.json)
		a = cb.cbUserList(request.json)
		return a
	else:
		return []

@app.route('/lastWsId')
def lastWsId():
    return cb.lastWs()

from flask import Flask

if __name__ == "__main__":
	app.run(debug = False , host="0.0.0.0" , port=8080)