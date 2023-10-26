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
import datetime
import time 
import uuid

from flask import Flask,render_template,request

class work():

	debug = True
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
		#self.readConfigFile(file)
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

	def readConfigFile(self,configFile):
		a = open(configFile, "rb" )
		
		if self.debug == True:
			ic(a.read())

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
		q = q +' AND u.dt BETWEEN $startDt AND $endDt ' 
		q = q + " AND u.`sgDb` IS NOT MISSING "
		q = q + ' AND u.`user` IS NOT MISSING '
		q = q + ' GROUP BY u.`sgDb` '

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
		q = 'SELECT u.`dt`,u.`user`,meta(u).id as cbKey, u.`dtDiffSec`,u.`cRow`,u.`qRow`,u.`tRow`,u.`conflicts`,u.`errors` FROM `'+self.cbBucketName+'`.`'+self.cbScopeName +'`.`'+ self.cbCollectionName+'` as u WHERE u.`docType` = "byWsId"'
		q = q +' AND u.dt BETWEEN $startDt AND $endDt ' 
		q = q + " AND u.`sgDb` = $sgDb "
		q = q + ' AND u.`user` IS NOT MISSING '

		if rangeData["errors"] and rangeData["errors"] == True:
			q = q + ' AND u.`errors` > 0 '

		if rangeData["conflicts"] and rangeData["conflicts"] == True:
			q = q + ' AND u.`conflicts` > 0 '
		
		if rangeData["sinceZero"] and rangeData["sinceZero"] == True:
			q = q + ' AND u.`since` = ["0"] '

		if rangeData["filterByChannels"] and rangeData["filterByChannels"] == True:
			q = q + ' AND ARRAY_LENGTH(u.`filterBy`) > 0 '

		if rangeData["syncTime"]:
			q = q + ' AND u.`dtDiffSec` >= TONUMBER('+rangeData["syncTime"]+') '

		if rangeData["changeCount"] :
			q = q + ' AND u.`tRow` >= TONUMBER('+rangeData["changeCount"]+') '

		if 'user' not in rangeData or not rangeData["user"]:
			q = q + ' AND u.`user` IS NOT MISSING '
		else:
			q = q + ' AND u.`user` = $user '

		q = q + ' ORDER BY u.dt DESC '
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
		q = q +' AND u.dt BETWEEN $startDt AND $endDt ' 
		q = q + ' AND u.`sgDb` = $sgDb '
		q = q + ' AND u.`user` IS NOT MISSING '
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
			return data
		except CouchbaseException:
			ic(traceback.format_exc())
			return []

	def cbSgDbList(self,rangeDate):
		return {}
	def cbLastWsId(self):
		return {}

cb = work()

app = Flask(__name__)

@app.route('/')
def hello():
    return render_template('index.html')

@app.route('/sgUserFind')
def sgUserFind():
    return 'Hello, World!'

@app.route('/dateRange', methods=['POST'])
def dateRange():
	if request.method == 'POST':
		ic(request.json)
		a = cb.cbDtRangeSearch(request.json)
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
    return 'Hello, World!'
from flask import Flask



if __name__ == "__main__":
	app.run(debug = True)

"""
	if len(sys.argv) > 1:
		configFile = sys.argv[1]
		a = work(configFile)
	else:
		print("Error: No config.json file given")
		exit()

"""