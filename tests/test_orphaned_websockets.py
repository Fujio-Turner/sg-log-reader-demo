#!/usr/bin/env python3
"""
Test script to demonstrate orphaned WebSocket detection and processing.
Creates test logs with orphaned WebSocket activity.
"""

import json
import os
import tempfile

def create_orphaned_websocket_test_log():
    """
    Create a test log that simulates orphaned WebSocket activity.
    This represents WebSocket connections that started before this log file.
    """
    
    log_lines = []
    
    # Add some regular log lines
    for i in range(10):
        log_lines.append(f'2024-01-15T10:30:{i:02d}.123Z [INF] Regular log line {i}')
    
    # Add a proper WebSocket connection (not orphaned)
    log_lines.append('2024-01-15T10:30:15.123Z [INF] HTTP: #001 POST /db/_blipsync <ud>known_user</ud>')
    log_lines.append('2024-01-15T10:30:15.124Z [DBG] BLIP+: #001 Upgraded to BLIP+WebSocket protocol [ws-known123]')
    log_lines.append('2024-01-15T10:30:15.125Z [DBG] BLIP+: [ws-known123] Processing changes for channel: channel1')
    log_lines.append('2024-01-15T10:30:15.126Z [DBG] BLIP+: [ws-known123] Sent 25 changes to client')
    
    # Add orphaned WebSocket activity (connections that started before this log)
    # These show WebSocket IDs but we never saw their initial _blipsync connection
    
    # Orphaned WebSocket 1 - appears to be doing active sync
    log_lines.append('2024-01-15T10:30:20.123Z [DBG] BLIP+: [ws-orphan001] GetCachedChanges("user_channel") got 150 changes')
    log_lines.append('2024-01-15T10:30:20.124Z [DBG] BLIP+: [ws-orphan001] Since:145 SyncMsg: continuous:true')
    log_lines.append('2024-01-15T10:30:20.125Z [DBG] BLIP+: [ws-orphan001] Sent 75 changes to client, from seq 145')
    log_lines.append('2024-01-15T10:30:20.126Z [DBG] BLIP+: [ws-orphan001] Filter:sync_gateway/bychannel Channels:user_channel,public')
    log_lines.append('2024-01-15T10:30:20.127Z [DBG] BLIP+: [ws-orphan001] Type:proposeChanges #Changes: 5')
    log_lines.append('2024-01-15T10:30:20.128Z [DBG] BLIP+: [ws-orphan001] CRUD: c:[abc123] doc updated')
    log_lines.append('2024-01-15T10:30:20.129Z [ERR] BLIP+: [ws-orphan001] 409 Document update conflict')
    
    # Orphaned WebSocket 2 - appears to be closing
    log_lines.append('2024-01-15T10:30:25.123Z [DBG] BLIP+: [ws-orphan002] GetChangesInChannel("admin") returned 25 changes')
    log_lines.append('2024-01-15T10:30:25.124Z [DBG] BLIP+: [ws-orphan002] Type:getAttachment Digest:sha1-xyz789')
    log_lines.append('2024-01-15T10:30:25.125Z [DBG] BLIP+: [ws-orphan002] proveAttachment successful for doc user_doc_456')
    log_lines.append('2024-01-15T10:30:25.126Z [DBG] BLIP+: [ws-orphan002] BLIP+WebSocket connection closed')
    
    # Orphaned WebSocket 3 - minimal activity
    log_lines.append('2024-01-15T10:30:30.123Z [WRN] BLIP+: [ws-orphan003] Error retrieving changes for channel restricted')
    log_lines.append('2024-01-15T10:30:30.124Z [DBG] BLIP+: [ws-orphan003] Since:0 SyncMsg: continuous:false')
    
    # More regular log lines
    for i in range(5):
        log_lines.append(f'2024-01-15T10:30:{35+i:02d}.123Z [INF] End log line {i}')
    
    return log_lines

def create_test_config(log_filename):
    """Create test configuration for orphaned WebSocket testing"""
    config = {
        "file-to-parse": log_filename,
        "cb-cluster-host": "127.0.0.1",
        "cb-bucket-name": "sg-log-reader-test",
        "cb-bucket-user": "Administrator",
        "cb-bucket-user-password": "fujiofujio",
        "debug": ["*"],  # Enable debug to see orphaned WebSocket detection
        "log-name": "orphaned-websocket-test",
        "cb-expire": 3600
    }
    return config

def analyze_expected_results():
    """Analyze what we expect to find in the test log"""
    print("Expected Results Analysis:")
    print("=" * 50)
    
    print("\n1. Known WebSocket (not orphaned):")
    print("   - ws-known123: Has initial _blipsync connection")
    print("   - User: known_user")
    print("   - Should be processed normally")
    
    print("\n2. Orphaned WebSocket 1 (ws-orphan001):")
    print("   - User: UNKNOWN:ws-orphan001")
    print("   - trackChange: True (has GetCachedChanges)")
    print("   - trackSince: True (has Since:145)")
    print("   - trackChannels: True (has channels: user_channel, public)")
    print("   - trackTiming: True")
    print("   - trackErrors: True (has conflict)")
    print("   - trackMetrics: True")
    print("   - Cache rows: 150")
    print("   - Sent count: 75")
    print("   - Push propose count: 5")
    print("   - Push count: 1")
    print("   - Conflicts: 1")
    print("   - Continuous: true")
    
    print("\n3. Orphaned WebSocket 2 (ws-orphan002):")
    print("   - User: UNKNOWN:ws-orphan002")
    print("   - trackChange: True (has GetChangesInChannel)")
    print("   - trackChannels: True (has admin channel)")
    print("   - Query rows: 25") 
    print("   - Pull att count: 1")
    print("   - Att success: 1")
    print("   - blip_closed: True")
    
    print("\n4. Orphaned WebSocket 3 (ws-orphan003):")
    print("   - User: UNKNOWN:ws-orphan003")
    print("   - trackSince: True (has Since:0)")
    print("   - trackErrors: True (has error)")
    print("   - Errors: 1")
    print("   - Continuous: false")
    
    print("\n5. Database Documents Created:")
    print("   - orphaned:ws-orphan001")
    print("   - orphaned:ws-orphan002") 
    print("   - orphaned:ws-orphan003")
    print("   - Plus normal WebSocket document for ws-known123")

def create_test_files():
    """Create test files for orphaned WebSocket testing"""
    
    print("Creating Orphaned WebSocket Test Files")
    print("=" * 40)
    
    # Create test log
    log_lines = create_orphaned_websocket_test_log()
    log_filename = "test_orphaned_websockets.log"
    
    with open(log_filename, 'w') as f:
        f.write('\n'.join(log_lines))
    
    # Create test config
    config = create_test_config(log_filename)
    config_filename = "test_orphaned_config.json"
    
    with open(config_filename, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"Created test files:")
    print(f"  Log file: {log_filename} ({len(log_lines)} lines)")
    print(f"  Config file: {config_filename}")
    
    print(f"\nTest log contains:")
    print(f"  - 1 known WebSocket (ws-known123)")
    print(f"  - 3 orphaned WebSockets (ws-orphan001, ws-orphan002, ws-orphan003)")
    print(f"  - Various WebSocket activities to test tracking capabilities")
    
    return log_filename, config_filename

def show_sample_log_lines():
    """Show sample lines that demonstrate orphaned WebSocket detection"""
    print("\nSample Log Lines:")
    print("-" * 20)
    
    lines = create_orphaned_websocket_test_log()
    
    print("Known WebSocket (has _blipsync):")
    for line in lines:
        if "_blipsync" in line or "ws-known123" in line:
            print(f"  {line}")
    
    print("\nOrphaned WebSocket Activity (no initial _blipsync):")
    for line in lines:
        if "ws-orphan" in line:
            print(f"  {line}")

if __name__ == "__main__":
    print("Orphaned WebSocket Detection Test")
    print("=" * 40)
    
    # Show what the test will do
    analyze_expected_results()
    
    # Show sample log lines
    show_sample_log_lines()
    
    # Create test files
    print("\n" + "=" * 50)
    log_file, config_file = create_test_files()
    
    print(f"\nTo test orphaned WebSocket detection, run:")
    print(f"   python sg_log_reader.py {config_file}")
    print(f"   python sg_log_reader_optimized.py {config_file}")
    
    print(f"\nLook for output:")
    print(f"   - 'Number - Orphaned WebSocket IDs found: 3'")
    print(f"   - 'Processing orphaned WebSockets...'")
    print(f"   - Debug output showing orphaned WebSocket detection")
    
    print(f"\nIn Couchbase, you should find documents:")
    print(f"   - orphaned:ws-orphan001 (with trackChange=true, trackSince=true)")
    print(f"   - orphaned:ws-orphan002 (with trackChange=true, blip_closed=true)")
    print(f"   - orphaned:ws-orphan003 (with trackSince=true, errors=1)")
    
    # Auto cleanup test files
    print("\nCleaning up test files...")
    for file in [log_file, config_file]:
        if os.path.exists(file):
            os.remove(file)
            print(f"Removed: {file}")
    print("✅ Orphaned WebSocket test completed successfully!")
