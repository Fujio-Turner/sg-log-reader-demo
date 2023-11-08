
import asyncio
from datetime import timedelta

import traceback

from couchbase.auth import PasswordAuthenticator
from acouchbase.cluster import Cluster
from couchbase.options import ClusterOptions
from couchbase.exceptions import CouchbaseException


import datetime 
import uuid

class work():

    logFile = "/Users/fujio.turner/Downloads/abc/pge/sg_info.log"
    logData = []
    cb  = None
    cbColl = None

    def __init__(self):
         self.makeCB()
         self.openSgLogFile()
    
    async def makeCB(self):
        try:
            auth = PasswordAuthenticator("Administrator", "fujiofujio")
            cluster = Cluster('couchbase://127.0.0.1', ClusterOptions(auth))
            cluster.wait_until_ready(timedelta(seconds=5))

            self.cb = cluster.bucket("sg-log-reader")
            #self.cbColl = self.cb.scope(self.cbScopeName).collection(self.cbCollectionName)
            self.cbColl = self.cb.default_collection()
            await self.cb.on_connect()

        except:
            print("Error: Could not connect to CB Cluster:" )
            exit()

    def openSgLogFile(self):
            print("Starting - Reading Data File: ",datetime.datetime.now())
            with open(self.logFile, "r") as a:
                b = [line.strip() for line in a.readlines()]

            for x in b:
                self.logData.append(x)

    def checkError(self,line):
         if "error" in line:
              #print(line)
              key = str(uuid.uuid1())
              #self.cbInsertA(key,line,600)
              return line

    def checkBlip(self,line):
         if "blip" in line:
              #print(line)
              key = str(uuid.uuid1())
              #self.cbInsertA(key,line,600)
              return line
         
    def cbInsert(self,key,doc,ttl=0):
        try:
            r = self.cbColl.insert(key,doc,expiry=timedelta(seconds=ttl))
            return r
        except CouchbaseException:
            print(traceback.format_exc())
            print("Error: Insert Key: ",key)
            return False
    
    async def cbInsertA(self,key,doc,ttl=0):
        try:
            r = await self.cbColl.insert(key,doc,expiry=timedelta(seconds=ttl))
        except CouchbaseException:
            print(traceback.format_exc())
            print("Error: Insert Key: ",key)
            return False
        

if __name__ == "__main__":
    start = datetime.datetime.now()
    a = work()
    
    for x in a.logData:
         a.checkError(x)
         a.checkBlip(x)
    end = datetime.datetime.now()
    print("THE END: ",datetime.datetime.now())
    difference = (end - start).total_seconds()
    print("Time difference in seconds:", difference)
    
	

'''
with cProfile.Profile() as pr:
    work()

stats = pstats.Stats(pr)
stats.sort_stats(pstats.SortKey.TIME)
stats.print_stats()
stats.dump_stats(filename="test3.prof")
'''