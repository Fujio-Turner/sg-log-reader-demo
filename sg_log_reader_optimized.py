# Version information
# 🤖 AI ASSISTANT HINT: Please increment this version number on every significant update/save
# Use semantic versioning: MAJOR.MINOR.PATCH (e.g., 1.0.0 -> 1.0.1 for fixes, 1.1.0 for features)
__version__ = "2.1.0"

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
from collections import defaultdict, deque
from typing import Dict, List, Optional, Tuple, Any

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
    
    # Pre-compiled regex patterns for performance
    WS_ID_PATTERN = re.compile(r"\[([A-Za-z0-9_]+)\]")
    DB_PATTERN = re.compile(r'/([^/]+)/_blipsync')
    USER_PATTERN = re.compile(r'<ud>(.*?)</ud>')
    USER_DETAIL_PATTERN = re.compile(r'<ud>\d+\.<ud>(.*?)</ud></ud>')
    REPLICATOR_PATTERN = re.compile(r"\[([A-Za-z0-9_-]+)\]")
    SINCE_PATTERN = re.compile(r'Since:(\S+)')
    CRUD_PATTERN = re.compile(r"\sCRUD:\sc:\[[a-f0-9]+\]\s")
    ROWS_PATTERN = re.compile(r'Got (\d+) rows')
    QUOTED_STRING_PATTERN = re.compile(r'for "([^"]+)"')
    
    cb = None
    sgLogName = "sg_info.log"
    cbHost = "127.0.0.1"
    cbUser = "Administrator"
    cbPass = "password"
    cbBucketName = "sg-log-reader"
    cbScopeName = "_default"
    cbCollectionName = "_default"
    cbColl = None
    
    # Memory efficient data structures
    wsIdList = {}
    wasBlipLines = False
    blipLineCount = 0
    oldWsDic = {}
    orphanedWsIds = {}  # Track orphaned WebSocket IDs found in logs
    orphanedWsLines = {}  # Store lines for orphaned WebSockets
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
    
    # Batch processing configuration
    BATCH_SIZE = 100
    cb_batch = []
    
    # Progress tracking
    processed_lines = 0
    total_lines = 0
    
    def __init__(self, file):
        asyncio.run(self.main(file))

    def __del__(self):
        sys.stdout = sys.__stdout__

    async def main(self, file):
        await self.readConfigFile(file)
        await self.debugIceCream()
        await self.makeCB()
        await self.get_file_size()
        await self.openSgLogFileOptimized()
        await self.flush_batch()  # Ensure any remaining batch items are processed

    async def get_file_size(self):
        """Get total file size for progress tracking"""
        if os.path.exists(self.sgLogName):
            with open(self.sgLogName, 'r') as f:
                self.total_lines = sum(1 for _ in f)
            print(f"Total lines to process: {self.total_lines:,}")

    async def makeCB(self):
        try:
            auth = PasswordAuthenticator(self.cbUser, self.cbPass)
            cluster = Cluster('couchbase://'+self.cbHost, ClusterOptions(auth))
            await cluster.wait_until_ready(timedelta(seconds=5))
            bucket = cluster.bucket(self.cbBucketName)
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
        with open(configFile, "rb") as a:
            b = json.loads(a.read())
        self.sgLogName = b["file-to-parse"]
        self.cbHost = b["cb-cluster-host"]
        self.cbBucket = b["cb-bucket-name"]
        self.cbUser = b["cb-bucket-user"]
        self.cbPass = b["cb-bucket-user-password"]
        self.debug = b["debug"]
        self.sgLogTag = b["log-name"]
        self.cbTtl = b['cb-expire']

    async def openSgLogFileOptimized(self):
        """Optimized file processing with streaming and batching"""
        print("Opening SG Log File: ", self.sgLogName)
        print("Starting - Reading Data File: ", datetime.datetime.now())
        
        if not os.path.exists(self.sgLogName):
            print("Error: File not found: ", self.sgLogName)
            exit()
            
        counter = 0
        
        # Process file line by line without loading into memory
        with open(self.sgLogName, "r", buffering=8192) as file:
            async for line_data in self.process_file_stream(file):
                counter += 1
                line, index = line_data
                
                # Progress tracking
                self.processed_lines = counter
                if counter % 10000 == 0:
                    progress = (counter / self.total_lines) * 100 if self.total_lines > 0 else 0
                    print(f"Progress: {counter:,}/{self.total_lines:,} lines ({progress:.1f}%)")
                
                if "*" in self.debug or "makeListRaw" in self.debug:
                    ic(counter, line)
                
                # Process line with all checks
                await self.process_line(line, index)
                
                # WebSocket tracking
                if self.wasBlipLines:
                    await self.findWsId(line, index)
                await self.findBlipLine(line, index)
                # Check for orphaned WebSocket activity
                await self.findOrphanedWsActivity(line, index)
                
        self.logNumberOflines = counter
        self.logLineDepthLevel = counter * self.logLineDepthPercent
        
        print("Number - Lines in log file: ", counter)
        print("Number - WebSocket Connections: ", self.blipLineCount)
        print("Number - Orphaned WebSocket IDs found: ", len(self.orphanedWsIds))
        print("Done - Reading Data File: ", datetime.datetime.now())
        
        if "*" in self.debug or "makeList" in self.debug:
            ic("makeListBig:",self.wsIdList)
            ic("Orphaned WebSockets:", self.orphanedWsIds)
            ic("Number - Lines in log file: ", counter)
            ic("Number - WebSocket Connections: ", self.blipLineCount)
            ic("Number - Orphaned WebSocket IDs: ", len(self.orphanedWsIds))

        # Process orphaned WebSockets first
        await self.processOrphanedWebSockets()
        await self.getDataPerWsIdOptimized()

    async def process_file_stream(self, file):
        """Generator that yields lines with index for memory efficiency"""
        index = 0
        for line in file:
            line = line.rstrip('\r\n')
            yield (line, index)
            index += 1

    async def process_line(self, line: str, index: int):
        """Process a single line with all checks"""
        # Use asyncio.gather for concurrent processing of independent checks
        await asyncio.gather(
            self.importCheck(line),
            self.sqlCheck(line),
            self.generalErrors(line),
            self.wsErrors(line),
            self.dcpChecks(line),
            return_exceptions=True
        )

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
            c = self.WS_ID_PATTERN.findall(wsLine)
            if len(c) > 1:
                userN = await self.getUserNameBlip(wsLine)
                httpNum = await self.httpTransNumPlus(wsLine)
                if httpNum+userN in self.wsIdList:
                    bline = self.wsIdList[httpNum+userN]
                    if "ws" not in bline:
                        bline["ws"] = c[1]
                        bline["startLine"] = index
                        bline["auth"] = True
                        self.wsIdList[httpNum+userN] = bline

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
        # Use pre-compiled patterns
        if "<ud>" in line and "</ud>" in line:
            db_match = self.DB_PATTERN.search(line)
            user_match = self.USER_PATTERN.search(line)
            
            if db_match and user_match:
                return [db_match.group(1), user_match.group(1)]

        # Fallback to splitting method
        c = line.split(" ")
        sgDb = c[6].split("/")[1]
        usrN = c[-1].rstrip(')')
        return [sgDb, usrN]

    async def getUserNameBlip(self, line):
        if "<ud>" in line and "</ud>" in line:
            match = self.USER_PATTERN.search(line)
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

    async def findOrphanedWsActivity(self, line, index):
        """
        Detect WebSocket activity for connections that started before this log file.
        Look for WebSocket IDs in brackets [ws-xxx] that aren't in our known wsIdList.
        """
        # Look for WebSocket IDs in square brackets
        ws_pattern = r'\[([ws-][A-Za-z0-9_-]+)\]'
        ws_matches = re.findall(ws_pattern, line)
        
        if ws_matches:
            for ws_id in ws_matches:
                # Check if this WebSocket ID is already known
                known_ws = False
                for key, ws_data in self.wsIdList.items():
                    if 'ws' in ws_data and ws_data['ws'] == ws_id:
                        known_ws = True
                        break
                
                # If not known, it's orphaned
                if not known_ws:
                    if "*" in self.debug or "makeList" in self.debug:
                        ic("Orphaned WebSocket found:", ws_id, line)
                    
                    # Initialize orphaned WebSocket tracking
                    if ws_id not in self.orphanedWsIds:
                        t = await self.getTimeFromLine(line)
                        isoDt = await self.iso8601_to_epoch(t[1])
                        
                        self.orphanedWsIds[ws_id] = {
                            "user": f"UNKNOWN:{ws_id}",
                            "sgDb": "unknown",
                            "auth": False,
                            "dt": t[0],
                            "dtFullEpoch": isoDt,
                            "ws": ws_id,
                            "startLine": index,
                            "orphaned": True,
                            "firstSeen": t[0],
                            "firstSeenEpoch": isoDt
                        }
                        self.orphanedWsLines[ws_id] = []
                    
                    # Store the line for this orphaned WebSocket
                    self.orphanedWsLines[ws_id].append(line)

    async def processOrphanedWebSockets(self):
        """
        Process all orphaned WebSockets and create documents for them.
        Include tracking flags for what metrics can/cannot be calculated.
        """
        print("Processing orphaned WebSockets...")
        
        for ws_id, ws_data in self.orphanedWsIds.items():
            if "*" in self.debug or "makeList" in self.debug:
                ic("Processing orphaned WebSocket:", ws_id)
            
            # Analyze what we can track for this orphaned WebSocket
            tracking_capabilities = await self.analyzeOrphanedWsCapabilities(ws_id)
            
            # Get first and last timestamps
            lines = self.orphanedWsLines.get(ws_id, [])
            if not lines:
                continue
                
            first_line = lines[0]
            last_line = lines[-1]
            
            tf = await self.getTimeFromLine(first_line)
            tl = await self.getTimeFromLine(last_line)
            
            # Calculate what we can
            df = None
            if tf[0] and tl[0]:
                try:
                    df = await self.diffdates(tf[0], tl[0])
                except:
                    df = None
            
            # Create orphaned WebSocket document
            orphaned_doc = {
                "docType": "byWsId",
                "user": ws_data["user"],
                "sgDb": ws_data["sgDb"],
                "sgColl": {},
                "dtFullEpoch": ws_data["dtFullEpoch"],
                "dt": ws_data["dt"],
                "dtEnd": tl[0] if tl[0] else ws_data["dt"],
                "dtDiffSec": df,
                "since": tracking_capabilities.get("since_values", []),
                "continuous": tracking_capabilities.get("continuous"),
                "conflicts": tracking_capabilities.get("conflicts", 0),
                "errors": tracking_capabilities.get("errors", 0),
                "warnings": tracking_capabilities.get("warnings", 0),
                "cRow": tracking_capabilities.get("cache_rows", 0),
                "qRow": tracking_capabilities.get("query_rows", 0),
                "tRow": tracking_capabilities.get("total_rows", 0),
                "attSuccess": tracking_capabilities.get("att_success", 0),
                "pullAttCount": tracking_capabilities.get("pull_att_count", 0),
                "pushCount": tracking_capabilities.get("push_count", 0),
                "pushProposeCount": tracking_capabilities.get("push_propose_count", 0),
                "pushAttCount": tracking_capabilities.get("push_att_count", 0),
                "sentCount": tracking_capabilities.get("sent_count", 0),
                "filterBy": tracking_capabilities.get("filter_by", False),
                "changesChannels": tracking_capabilities.get("channels", []),
                "logTag": self.sgLogTag,
                "blipC": tracking_capabilities.get("blip_closed", False),
                "blipO": tracking_capabilities.get("blip_opened", False),
                "auth": False,
                "orphaned": True,
                "firstSeen": ws_data["firstSeen"],
                "firstSeenEpoch": ws_data["firstSeenEpoch"],
                "lineCount": len(lines),
                
                # Tracking capabilities flags
                "trackChange": tracking_capabilities.get("can_track_changes", False),
                "trackSince": tracking_capabilities.get("can_track_since", False),
                "trackChannels": tracking_capabilities.get("can_track_channels", False),
                "trackTiming": tracking_capabilities.get("can_track_timing", True),
                "trackErrors": tracking_capabilities.get("can_track_errors", True),
                "trackMetrics": tracking_capabilities.get("can_track_metrics", True),
                
                # Store limited log lines (not all to save space)
                "log": lines[:100] if len(lines) > 100 else lines  # Limit to first 100 lines
            }
            
            # Use batch upsert for performance
            key = f"orphaned:{ws_id}"
            await self.batch_upsert(key, orphaned_doc, self.cbTtl)
            
            if "*" in self.debug or "makeList" in self.debug:
                ic("Orphaned WebSocket processed:", ws_id, "lines:", len(lines))

    async def analyzeOrphanedWsCapabilities(self, ws_id):
        """
        Analyze what metrics can be tracked for an orphaned WebSocket
        based on the log lines we have.
        """
        lines = self.orphanedWsLines.get(ws_id, [])
        
        capabilities = {
            "can_track_changes": False,
            "can_track_since": False,
            "can_track_channels": False,
            "can_track_timing": True,  # We can always track timing from available lines
            "can_track_errors": True,  # We can always count errors
            "can_track_metrics": True,  # We can track basic metrics
            "since_values": [],
            "channels": [],
            "cache_rows": 0,
            "query_rows": 0,
            "total_rows": 0,
            "conflicts": 0,
            "errors": 0,
            "warnings": 0,
            "sent_count": 0,
            "pull_att_count": 0,
            "push_count": 0,
            "push_propose_count": 0,
            "push_att_count": 0,
            "att_success": 0,
            "continuous": None,
            "filter_by": False,
            "blip_closed": False,
            "blip_opened": False
        }
        
        channels_found = set()
        
        for line in lines:
            # Check for various patterns and update capabilities
            
            # Since values
            if "Since:" in line and "SyncMsg:" in line:
                capabilities["can_track_since"] = True
                if "Since:0 " in line:
                    capabilities["since_values"].append("0")
                else:
                    since_val = await self.findSince(line)
                    if since_val:
                        capabilities["since_values"].append(since_val)
            
            # Channel information
            if "GetCachedChanges(\"" in line or "GetChangesInChannel(" in line:
                capabilities["can_track_changes"] = True
                capabilities["can_track_channels"] = True
                
                if "GetCachedChanges(\"" in line:
                    try:
                        c = await self.changeCacheCount(line)
                        capabilities["cache_rows"] += c[0]
                        channels_found.add(c[1])
                    except:
                        pass
                        
                if "GetChangesInChannel(" in line:
                    try:
                        d = await self.changeQueryCount(line)
                        capabilities["query_rows"] += d[0]
                        channels_found.add(d[1])
                    except:
                        pass
            
            # Filter information
            if "Filter:sync_gateway/bychannel" in line:
                capabilities["filter_by"] = True
                try:
                    filter_channels = await self.findChannelsList(line)
                    channels_found.update(filter_channels)
                except:
                    pass
            
            # Continuous replication
            if " Continuous:" in line and " SyncMsg:" in line:
                try:
                    capabilities["continuous"] = await self.findContinuous(line)
                except:
                    pass
            
            # Metrics we can always track
            if " changes to client, from seq " in line:
                try:
                    j = await self.findSentCount(line)
                    capabilities["sent_count"] += j
                except:
                    pass
                    
            if " proveAttachment successful for doc " in line:
                capabilities["att_success"] += 1
                
            if "Type:getAttachment Digest:" in line:
                capabilities["pull_att_count"] += 1
                
            if "Type:proposeChanges" in line:
                try:
                    p = await self.findPushCount(line)
                    capabilities["push_propose_count"] += p
                except:
                    pass
                    
            if "Added attachment" in line and "CRUD:" in line:
                capabilities["push_att_count"] += 1
                
            if self.CRUD_PATTERN.search(line):
                capabilities["push_count"] += 1
                
            if "409 Document update conflict" in line:
                capabilities["conflicts"] += 1
                
            if "[ERR]" in line or "Error retrieving changes for channel" in line:
                capabilities["errors"] += 1
                
            if "Error " in line and ".go:" in line and "[WRN]" not in line:
                capabilities["errors"] += 1
                
            if 'error' in line.lower():
                capabilities["errors"] += 1
                
            if "[WRN]" in line:
                capabilities["warnings"] += 1
                
            # Connection state
            if "BLIP+WebSocket connection closed" in line:
                capabilities["blip_closed"] = True
                
            if "Upgraded to" in line and "WebSocket protocol" in line:
                capabilities["blip_opened"] = True
        
        # Set channels
        capabilities["channels"] = sorted(list(channels_found))
        capabilities["total_rows"] = capabilities["cache_rows"] + capabilities["query_rows"]
        
        # Determine if we have enough data for meaningful change tracking
        if capabilities["cache_rows"] > 0 or capabilities["query_rows"] > 0:
            capabilities["can_track_changes"] = True
            
        if len(capabilities["channels"]) > 0:
            capabilities["can_track_channels"] = True
        
        return capabilities

    async def getDataPerWsIdOptimized(self):
        """Optimized WebSocket data processing with batching"""
        print("Starting - Per wsId : ", datetime.datetime.now())
        
        # Process in smaller concurrent batches to avoid memory overload
        batch_size = 50  # Smaller batch size for large datasets
        ws_items = list(self.wsIdList.items())
        
        for i in range(0, len(ws_items), batch_size):
            batch = ws_items[i:i + batch_size]
            tasks = [self.getDataPerWsIdWorker(x[1]) for x in batch]
            
            try:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results and handle exceptions
                for idx, res in enumerate(results):
                    if isinstance(res, BaseException):
                        print(f"Task {i + idx} raised an exception: {res}")
                
                # Small delay to prevent overwhelming the system
                if i + batch_size < len(ws_items):
                    await asyncio.sleep(0.1)
                    
            except Exception as e:
                print(f"Batch processing error: {e}")
                continue

        print("Done - Per wsId :", datetime.datetime.now())

    async def getDataPerWsIdWorker(self, x):
        """Optimized worker with streaming log processing"""
        sinceList = []
        if x["auth"]:
            w = x["ws"]
            r = await self.loopLogOptimized(x["ws"], x["startLine"], sinceList)
            
            if not r[0]:  # No log data found
                return [w, None]
                
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
        
        # Use batch upsert instead of individual operations
        await self.batch_upsert(w, d, self.cbTtl)
        return [w, d]

    async def loopLogOptimized(self, wsId: str, startLogLine: int, sinceList: List):
        """Memory-efficient log processing without loading entire file"""
        logLine = []
        stats = {
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
        
        # Process file in streaming fashion for this WebSocket
        line_count = 0
        with open(self.sgLogName, "r", buffering=8192) as file:
            # Skip to start line efficiently
            for _ in range(startLogLine):
                try:
                    next(file)
                    line_count += 1
                except StopIteration:
                    break
            
            # Process remaining lines with safety checks
            for line in file:
                line_count += 1
                line = line.rstrip('\r\n')
                
                # Calculate remaining lines for boundary checking
                current_position = startLogLine + line_count - 1
                remaining_lines = max(0, self.logNumberOflines - current_position)
                
                if wsId in line and "WS" not in line:
                    if "*" in self.debug or "wsId" in self.debug:
                        ic("WSID found in line : ", wsId, line)
                    if not stats['blipClosed']:
                        stats['passIt'] = 0
                    
                    logLine.append(line)
                    
                    # Process line with optimized pattern matching
                    await self.process_ws_line(line, stats)
                    
                    # Check for connection close
                    if "BLIP+WebSocket connection closed" in line:
                        # Calculate safe scan depth to avoid going beyond file end
                        scan_depth = min(self.logScanDepthAfterClose, remaining_lines)
                        stats['passIt'] = self.logLineDepthLevel - scan_depth
                        stats['blipClosed'] = True
                        continue
                    if "Upgraded to" in line and "WebSocket protocol" in line:
                        stats['blipOpened'] = True
                        continue
                else:
                    stats['passIt'] += 1
                
                if stats['passIt'] >= self.logLineDepthLevel:
                    break
                    
                # Memory management for very long sessions
                if len(logLine) > 10000:  # Limit log line storage
                    logLine = logLine[-5000:]  # Keep last 5000 lines

        # Sort and return results
        stats['filterByChannels'].sort()
        stats['changesChannels'] = sorted(stats['changesChannels'].keys())
        
        return [
            logLine, stats['since'], stats['channelRow'], stats['queryRow'], 
            stats['filterBy'], stats['filterByChannels'], stats['blipClosed'], 
            stats['blipOpened'], stats['continuous'], stats['conflictCount'], 
            stats['errorCount'], stats['warningCount'], stats['sent'], 
            stats['pushAttachCount'], stats['pushCount'], stats['attSuc'], 
            stats['changesChannels'], stats['pullAttCount'], stats['pushProposeCount']
        ]

    async def process_ws_line(self, line: str, stats: Dict):
        """Process individual WebSocket line with optimized pattern matching"""
        
        # Cache check - changes making
        if "GetCachedChanges(\"" in line:
            c = await self.changeCacheCount(line)
            stats['channelRow'] += c[0]
            stats['changesChannels'][c[1]] = True
            return
            
        if "GetChangesInChannel(" in line:
            d = await self.changeQueryCount(line)					
            stats['queryRow'] += d[0]
            stats['changesChannels'][d[1]] = True
            return

        if "rows from query for " in line:
            d = await self.changeQueryCountByRow(line)					
            stats['queryRow'] += d[0]
            stats['changesChannels'][d[1]] = True
            return

        if " Continuous:" in line and " SyncMsg:" in line:
            stats['continuous'] = await self.findContinuous(line)

        if "Filter:sync_gateway/bychannel" in line:
            stats['filterBy'] = True
            stats['filterByChannels'] = await self.findChannelsList(line)

        if " changes to client, from seq " in line:		
            j = await self.findSentCount(line)
            stats['sent'] += j
            return
            
        if " proveAttachment successful for doc " in line:		
            stats['attSuc'] += 1
            return
            
        if "Type:getAttachment Digest:" in line:		
            stats['pullAttCount'] += 1
            return

        # Push from CBL 
        if "Type:proposeChanges" in line:
            p = await self.findPushCount(line)
            stats['pushProposeCount'] += p
            return

        if "Added attachment" in line and "CRUD:" in line:
            stats['pushAttachCount'] += 1
            return

        if self.CRUD_PATTERN.search(line):
            stats['pushCount'] += 1
            return

        if "409 Document update conflict" in line:
            stats['conflictCount'] += 1
            return
            
        if "[ERR]" in line or "Error retrieving changes for channel" in line:
            stats['errorCount'] += 1
            return

        if "Error " in line and ".go:" in line and "[WRN]" not in line: 
            stats['errorCount'] += 1
            return

        if 'error' in line.lower():
            stats['errorCount'] += 1

        if "[WRN]" in line:
            stats['warningCount'] += 1
            return
            
        if "Since:" in line and "SyncMsg:" in line:
            if "Since:0 " in line:
                stats['since'] = "0"
            else:
                stats['since'] = await self.findSince(line)

    async def batch_upsert(self, key: str, doc: Dict, ttl: int = 0):
        """Batch Couchbase operations for better performance"""
        self.cb_batch.append((key, doc, ttl))
        
        if len(self.cb_batch) >= self.BATCH_SIZE:
            await self.flush_batch()

    async def flush_batch(self):
        """Flush pending batch operations to Couchbase"""
        if not self.cb_batch:
            return
            
        try:
            # Process batch in parallel
            tasks = []
            for key, doc, ttl in self.cb_batch:
                task = self.cbUpsert(key, doc, ttl)
                tasks.append(task)
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            
            self.cb_batch.clear()
            
        except Exception as e:
            print(f"Batch flush error: {e}")
            self.cb_batch.clear()

    async def changeCacheCount(self, line):
        a = line.split(" ")
        b = line.split('GetCachedChanges("')

        match = self.USER_DETAIL_PATTERN.search(b[1]) #POST SG 3.1
        
        if match:
            return [int(a[8]),match.group(1)]
        
        c = b[1].split('"')
        
        if a[7] == "got":
            return [int(a[8]),c[0]]
        else:
            return [int(a[7]),c[0]]

    async def changeQueryCount(self, line):
        a = line.split(" ")

        if "<ud>" in a[5]:
            match = self.USER_DETAIL_PATTERN.search(a[5])  # POST SG 3.1

            if match:
                return [int(a[7]),match.group(1)]
        else:
            b = line.split('GetChangesInChannel("')  # PRE SG 3.1
            c = b[1].split('"')
            return [int(a[6]),c[0]]

    async def changeQueryCountByRow(self,line):
        number = self.ROWS_PATTERN.search(line).group(1)  
        quoted_string = self.QUOTED_STRING_PATTERN.search(line).group(1)  
        return [int(number), quoted_string]

    async def getTimeFromLine(self, line):
        return [line[0+self.sgDtLineOffset:19+self.sgDtLineOffset].rstrip("-"), line[0+self.sgDtLineOffset:24+self.sgDtLineOffset].rstrip("-")]

    async def sgStarts(self, x):
        if "==== Couchbase Sync Gateway/" in x:
            t = await self.getTimeFromLine(x)
            d = {"docType":"sgStart","dt":t[0], "tag":self.sgLogTag}
            await self.batch_upsert(self.sgLogTag+"::sgStart::"+t[0], d, self.cbTtl)

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
            d[errorElement] += 1
            e = await self.batch_upsert(key, d, self.cbTtl)
            return e
        else:
            isoDt = await self.iso8601_to_epoch(dtFullEpoch)
            j = {"docType":"sgErrors", "dt":dt, "dtFullEpoch":isoDt, "import":0, "dcp":0, "query":0, "sgDb":0, "ws":0, "gen":0}
            j[errorElement] += 1
            f = await self.batch_upsert(key, j, self.cbTtl)
            return f

    async def findSentCount(self, x):
        a = x.split(" ")
        if a[5] == "Sent":
            return int(a[6])  #Post SG 3.1
        else:
            return int(a[5])  #Pre SG 3.1
    
    async def findPushCount(self, x):
        a = x.split("#Changes: ")
        return int(a[1])
    
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

    async def findSince(self, line):
        match = self.SINCE_PATTERN.search(line)
        if match:
            return match.group(1)
        else:
            return ""

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
            
        try:
            r = await self.cbColl.insert(key, doc, expiry=timedelta(seconds=ttl))
            if "*" in self.debug or "cb" in self.debug:
                ic(r)
            return r
        except CouchbaseException:
            ic(traceback.format_exc())
            ic("Error: Insert Key: ", key)
            return False
        
    async def cbUpsert(self, key, doc, ttl=0):
        if "*" in self.debug or "cb" in self.debug:
            ic("CB Upsert: Key:", key, "Doc:", doc)
        try:
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

if __name__ == "__main__":
    if len(sys.argv) > 1:
        configFile = sys.argv[1]
    else:
        print("Error: No config.json file given")
        exit()

    a = work(configFile)
    del a
