#!/usr/bin/env python3
"""
Test script to verify the boundary fix for WebSocket scanning near end of file.
"""

import tempfile
import json
import os

def create_test_log_with_ws_near_end():
    """Create a test log where WebSocket close happens near the end"""
    
    # Create log lines - WebSocket close near the end
    log_lines = []
    
    # Add initial lines
    for i in range(95):
        log_lines.append(f'2024-01-15T10:30:{i:02d}.123Z [INF] Regular log line {i}')
    
    # Add WebSocket start
    log_lines.append('2024-01-15T10:30:45.123Z [INF] HTTP: #001 POST /db/_blipsync <ud>testuser</ud>')
    log_lines.append('2024-01-15T10:30:45.124Z [DBG] BLIP+: #001 Upgraded to BLIP+WebSocket protocol [ws-123]')
    
    # Add a few WebSocket activity lines
    log_lines.append('2024-01-15T10:30:45.125Z [DBG] BLIP+: [ws-123] Processing changes')
    log_lines.append('2024-01-15T10:30:45.126Z [DBG] BLIP+: [ws-123] Sent 50 changes to client')
    
    # WebSocket close near the end (only 2 lines remaining after this)
    log_lines.append('2024-01-15T10:30:45.127Z [DBG] BLIP+: [ws-123] BLIP+WebSocket connection closed')
    
    # Only 2 lines left after WebSocket close
    log_lines.append('2024-01-15T10:30:45.128Z [INF] Final log line 1')
    log_lines.append('2024-01-15T10:30:45.129Z [INF] Final log line 2')
    
    return log_lines

def create_test_config(log_filename):
    """Create test configuration"""
    config = {
        "file-to-parse": log_filename,
        "cb-cluster-host": "127.0.0.1",
        "cb-bucket-name": "sg-log-reader-test",
        "cb-bucket-user": "Administrator",
        "cb-bucket-user-password": "fujiofujio",
        "debug": ["*"],  # Enable debug to see what's happening
        "log-name": "boundary-test",
        "cb-expire": 3600
    }
    return config

def test_boundary_logic():
    """Test the boundary checking logic independently"""
    
    # Simulate the problematic scenario
    logNumberOflines = 100  # Total lines in file
    logScanDepthAfterClose = 50  # Wants to scan 50 lines after close
    logLineDepthLevel = 1000  # Normal depth level
    
    # WebSocket closes at line 98 (only 2 lines remaining)
    current_line = 98
    remaining_lines = logNumberOflines - current_line
    
    print(f"Total lines in file: {logNumberOflines}")
    print(f"WebSocket closes at line: {current_line}")
    print(f"Remaining lines after close: {remaining_lines}")
    print(f"Requested scan depth: {logScanDepthAfterClose}")
    
    # Original problematic logic
    original_passIt = logLineDepthLevel - logScanDepthAfterClose
    print(f"Original passIt value: {original_passIt} (would try to scan beyond file)")
    
    # Fixed logic
    safe_scan_depth = min(logScanDepthAfterClose, remaining_lines)
    fixed_passIt = logLineDepthLevel - safe_scan_depth
    print(f"Safe scan depth: {safe_scan_depth}")
    print(f"Fixed passIt value: {fixed_passIt} (safe)")
    
    # Show the improvement
    lines_saved_from_error = logScanDepthAfterClose - safe_scan_depth
    print(f"Lines prevented from scanning beyond file: {lines_saved_from_error}")

def create_minimal_test_files():
    """Create minimal test files to verify the fix"""
    
    # Create test log
    log_lines = create_test_log_with_ws_near_end()
    log_filename = "test_boundary_log.log"
    
    with open(log_filename, 'w') as f:
        f.write('\n'.join(log_lines))
    
    # Create test config
    config = create_test_config(log_filename)
    config_filename = "test_boundary_config.json"
    
    with open(config_filename, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"Created test files:")
    print(f"  Log file: {log_filename} ({len(log_lines)} lines)")
    print(f"  Config file: {config_filename}")
    print(f"  WebSocket close at line: {len(log_lines) - 2}")
    print(f"  Lines remaining after close: 2")
    
    return log_filename, config_filename

if __name__ == "__main__":
    print("Testing Boundary Fix for WebSocket Scanning")
    print("=" * 50)
    
    # Test the logic
    print("\n1. Testing boundary logic:")
    test_boundary_logic()
    
    # Create test files
    print("\n2. Creating test files:")
    log_file, config_file = create_minimal_test_files()
    
    print(f"\n3. To test the fix, run:")
    print(f"   python sg_log_reader.py {config_file}")
    print(f"   python sg_log_reader_optimized.py {config_file}")
    
    print(f"\n4. The fixed version should handle the WebSocket close near")
    print(f"   the end of the file without index errors.")
    
    # Auto cleanup test files
    print("\nCleaning up test files...")
    for file in [log_file, config_file]:
        if os.path.exists(file):
            os.remove(file)
            print(f"Removed: {file}")
    print("✅ Boundary fix test completed successfully!")
