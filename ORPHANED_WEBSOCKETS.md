# Orphaned WebSocket Detection and Processing

## Overview

The enhanced log reader now detects and processes "orphaned" WebSocket connections - these are WebSocket activities found in log files where the initial `_blipsync` connection occurred before the current log file (e.g., due to log rotation).

## The Problem

In production Sync Gateway deployments:
1. WebSocket connections can span multiple hours or days
2. Log files are rotated (daily, weekly, or by size)
3. A WebSocket connection might start in one log file and continue in the next
4. You see WebSocket activity `[ws-xyz123]` but no initial `_blipsync` connection
5. Without the initial connection, you can't map the WebSocket ID to a user
6. These "orphaned" activities were previously ignored, losing valuable metrics

## The Solution

### Orphaned WebSocket Detection
The system now:
1. **Scans for WebSocket IDs** in log lines using pattern `[ws-xxxxx]`
2. **Checks against known WebSockets** from `_blipsync` connections
3. **Identifies orphaned WebSockets** that don't have initial connections
4. **Creates user entries** with format `UNKNOWN:{websocket_id}`
5. **Tracks available metrics** with capability flags

### Smart Capability Analysis
For each orphaned WebSocket, the system determines what can be tracked:

```json
{
  "trackChange": true,     // Can track change feeds (has GetCachedChanges/GetChangesInChannel)
  "trackSince": true,      // Can track since values (has Since: lines)
  "trackChannels": true,   // Can track channels (has channel information)
  "trackTiming": true,     // Can track timing (always possible from available lines)
  "trackErrors": true,     // Can track errors (always possible)
  "trackMetrics": true     // Can track basic metrics (always possible)
}
```

## Example Scenarios

### Scenario 1: Active Sync Session (Mid-Connection)
```
[DBG] BLIP+: [ws-abc123] GetCachedChanges("user_channel") got 150 changes
[DBG] BLIP+: [ws-abc123] Since:145 SyncMsg: continuous:true
[DBG] BLIP+: [ws-abc123] Sent 75 changes to client, from seq 145
```

**Result**: `UNKNOWN:ws-abc123` with full tracking capabilities
- trackChange: true, trackSince: true, trackChannels: true
- Cache rows: 150, Sent count: 75, Since: ["145"]

### Scenario 2: Connection Closing
```
[DBG] BLIP+: [ws-def456] Type:getAttachment Digest:sha1-xyz789
[DBG] BLIP+: [ws-def456] BLIP+WebSocket connection closed
```

**Result**: `UNKNOWN:ws-def456` with limited tracking
- trackTiming: true, trackMetrics: true
- Pull att count: 1, blip_closed: true

### Scenario 3: Error-Only Activity
```
[ERR] BLIP+: [ws-ghi789] 409 Document update conflict
[WRN] BLIP+: [ws-ghi789] Error retrieving changes for channel restricted
```

**Result**: `UNKNOWN:ws-ghi789` with error tracking
- trackErrors: true, Conflicts: 1, Errors: 1

## Database Storage

### Document Structure
Orphaned WebSockets are stored with key `orphaned:{websocket_id}`:

```json
{
  "docType": "byWsId",
  "user": "UNKNOWN:ws-abc123",
  "sgDb": "unknown",
  "orphaned": true,
  "auth": false,
  
  // Timing information
  "dt": "2024-01-15T10:30:20",
  "dtEnd": "2024-01-15T10:31:45", 
  "dtDiffSec": 85,
  "firstSeen": "2024-01-15T10:30:20",
  "firstSeenEpoch": 1705314620,
  
  // Tracked metrics (what was available)
  "cRow": 150,
  "qRow": 25,
  "tRow": 175,
  "sentCount": 75,
  "pushCount": 3,
  "conflicts": 1,
  "errors": 2,
  "since": ["145", "150"],
  "changesChannels": ["user_channel", "public"],
  
  // Capability flags
  "trackChange": true,
  "trackSince": true,
  "trackChannels": true,
  "trackTiming": true,
  "trackErrors": true,
  "trackMetrics": true,
  
  // Metadata
  "lineCount": 47,
  "logTag": "production-logs",
  "log": ["...", "first 100 log lines", "..."]
}
```

## Usage and Queries

### Finding Orphaned WebSockets
```sql
-- In Couchbase Query
SELECT user, lineCount, trackChange, trackSince, cRow, qRow, errors
FROM `sg-log-reader` 
WHERE docType = "byWsId" AND orphaned = true
ORDER BY firstSeenEpoch DESC;
```

### High-Activity Orphaned Sessions
```sql
SELECT user, cRow + qRow as totalRows, sentCount, pushCount
FROM `sg-log-reader`
WHERE docType = "byWsId" AND orphaned = true AND trackChange = true
ORDER BY totalRows DESC
LIMIT 20;
```

### Error Analysis
```sql
SELECT user, errors, conflicts, warnings, trackErrors
FROM `sg-log-reader`
WHERE docType = "byWsId" AND orphaned = true AND errors > 0
ORDER BY errors DESC;
```

## Configuration

No additional configuration needed. Orphaned WebSocket detection runs automatically.

### Debug Output
Enable debug to see orphaned WebSocket detection:
```json
{
  "debug": ["*"]
}
```

Output will show:
```
Orphaned WebSocket found: ws-abc123 [DEBUG LINE]
Processing orphaned WebSocket: ws-abc123
Number - Orphaned WebSocket IDs found: 15
```

## Benefits

1. **Complete Visibility**: See all WebSocket activity, not just connections that started in current log
2. **Production Insights**: Understand long-running connections that span log rotations  
3. **Error Tracking**: Capture errors from orphaned connections
4. **Performance Metrics**: Track change feeds, attachments, and sync performance
5. **User Behavior**: Understand usage patterns even without full connection data

## Limitations

For orphaned WebSockets, the system cannot determine:
- **Actual username** (shows as `UNKNOWN:{ws_id}`)
- **Connection start time** (only shows first activity in current log)
- **Initial sync parameters** (channels, since values before this log)
- **Authentication details**

However, it can track all activity from the current log file onward.

## Post-Processing Opportunities

Future enhancements could include:
1. **Cross-log correlation**: Match orphaned WebSockets across multiple log files
2. **User inference**: Try to determine actual usernames from channel patterns
3. **Connection reconstruction**: Rebuild full connection timelines
4. **Metrics aggregation**: Combine orphaned and known connection metrics

## Testing

Test orphaned WebSocket detection:
```bash
python test_orphaned_websockets.py
```

This creates test logs with known and orphaned WebSocket activities to verify the detection and processing logic.
