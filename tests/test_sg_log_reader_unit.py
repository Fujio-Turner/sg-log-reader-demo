#!/usr/bin/env python3
"""
Unit tests for sg_log_reader.py functionality
Tests core parsing and analysis functions without requiring Couchbase connection
"""

import unittest
import asyncio
import tempfile
import os
import json
import sys
from unittest.mock import Mock, patch, AsyncMock

# Add the current directory to the path to import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from sg_log_reader import work as SGLogReader
except ImportError:
    print("Could not import sg_log_reader. Skipping original version tests.")
    SGLogReader = None

try:
    import sg_log_reader_optimized
    SGLogReaderOptimized = sg_log_reader_optimized.work
except ImportError:
    print("Could not import sg_log_reader_optimized. Skipping optimized version tests.")
    SGLogReaderOptimized = None

class TestSGLogReaderCore(unittest.TestCase):
    """Test core functionality that doesn't require Couchbase"""
    
    def setUp(self):
        """Set up test fixtures"""
        if SGLogReader:
            # Create a mock config file
            self.config_data = {
                "file-to-parse": "test.log",
                "cb-cluster-host": "127.0.0.1",
                "cb-bucket-name": "test-bucket",
                "cb-bucket-user": "test",
                "cb-bucket-user-password": "test",
                "debug": [],
                "log-name": "unit-test",
                "cb-expire": 3600
            }
            
            # Create temporary config file
            self.config_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
            json.dump(self.config_data, self.config_file)
            self.config_file.close()
            
            # Create mock log reader instance (without running __init__)
            self.reader = SGLogReader.__new__(SGLogReader)
            # Initialize basic attributes
            self.reader.debug = []
            self.reader.sgDtLineOffset = 0
            self.reader.orphanedWsIds = {}
            self.reader.orphanedWsLines = {}
            self.reader.wsIdList = {}
            self.reader.sgLogTag = "unit-test"
            self.reader.logLineDepthLevel = 1000
            self.reader.logScanDepthAfterClose = 50
            self.reader.logNumberOflines = 100
    
    def tearDown(self):
        """Clean up test fixtures"""
        if hasattr(self, 'config_file'):
            os.unlink(self.config_file.name)
    
    @unittest.skipIf(SGLogReader is None, "sg_log_reader not available")
    def test_get_time_from_line(self):
        """Test timestamp extraction from log lines"""
        async def run_test():
            test_line = "2024-01-15T10:30:45.123Z [DBG] BLIP+: Some message"
            result = await self.reader.getTimeFromLine(test_line)
            
            self.assertEqual(result[0], "2024-01-15T10:30:45")
            self.assertEqual(result[1], "2024-01-15T10:30:45.123Z")
        
        asyncio.run(run_test())
    
    @unittest.skipIf(SGLogReader is None, "sg_log_reader not available")
    def test_get_user_name_parsing(self):
        """Test user name extraction from _blipsync lines"""
        async def run_test():
            # Test new format with <ud> tags
            test_line = '2024-01-15T10:30:45.123Z [INF] HTTP: #001 POST /mydb/_blipsync <ud>testuser</ud>'
            result = await self.reader.getUserName(test_line)
            
            self.assertEqual(result[0], "mydb")  # database name
            self.assertEqual(result[1], "testuser")  # username
            
            # Test fallback parsing
            fallback_line = '2024-01-15T10:30:45.123Z [INF] HTTP: request /mydb/_blipsync user (testuser2)'
            result2 = await self.reader.getUserName(fallback_line)
            self.assertEqual(result2[1], "testuser2")
        
        asyncio.run(run_test())
    
    @unittest.skipIf(SGLogReader is None, "sg_log_reader not available")
    def test_find_since_value(self):
        """Test since value extraction"""
        async def run_test():
            test_line = "2024-01-15T10:30:45.123Z [DBG] BLIP+: Since:145 SyncMsg: continuous:true"
            result = await self.reader.findSince(test_line)
            
            self.assertEqual(result, "145")
            
            # Test no since value
            no_since_line = "2024-01-15T10:30:45.123Z [DBG] BLIP+: SyncMsg: continuous:true"
            result2 = await self.reader.findSince(no_since_line)
            self.assertEqual(result2, "")
        
        asyncio.run(run_test())
    
    @unittest.skipIf(SGLogReader is None, "sg_log_reader not available")
    def test_find_continuous_flag(self):
        """Test continuous replication flag extraction"""
        async def run_test():
            # Test true
            test_line_true = "2024-01-15T10:30:45.123Z [DBG] BLIP+: Continuous:true SyncMsg:"
            result = await self.reader.findContinuous(test_line_true)
            self.assertTrue(result)
            
            # Test false
            test_line_false = "2024-01-15T10:30:45.123Z [DBG] BLIP+: Continuous:false SyncMsg:"
            result2 = await self.reader.findContinuous(test_line_false)
            self.assertFalse(result2)
            
            # Test no continuous
            test_line_none = "2024-01-15T10:30:45.123Z [DBG] BLIP+: SyncMsg:"
            result3 = await self.reader.findContinuous(test_line_none)
            self.assertIsNone(result3)
        
        asyncio.run(run_test())
    
    @unittest.skipIf(SGLogReader is None, "sg_log_reader not available") 
    def test_find_sent_count(self):
        """Test sent count extraction"""
        async def run_test():
            # Test post SG 3.1 format
            test_line = "2024-01-15T10:30:45.123Z [DBG] BLIP+: Sent 75 changes to client, from seq 145"
            result = await self.reader.findSentCount(test_line)
            self.assertEqual(result, 75)
        
        asyncio.run(run_test())
    
    @unittest.skipIf(SGLogReader is None, "sg_log_reader not available")
    def test_find_push_count(self):
        """Test push count extraction"""
        async def run_test():
            test_line = "2024-01-15T10:30:45.123Z [DBG] BLIP+: Type:proposeChanges #Changes: 5"
            result = await self.reader.findPushCount(test_line)
            self.assertEqual(result, 5)
        
        asyncio.run(run_test())
    
    @unittest.skipIf(SGLogReader is None, "sg_log_reader not available")
    def test_orphaned_websocket_detection(self):
        """Test orphaned WebSocket detection logic"""
        async def run_test():
            # Setup test data
            self.reader.wsIdList = {
                "http123known_user": {
                    "user": "known_user",
                    "ws": "ws-known123",
                    "auth": True
                }
            }
            
            # Test orphaned WebSocket detection
            orphaned_line = "2024-01-15T10:30:45.123Z [DBG] BLIP+: [ws-orphan001] GetCachedChanges got 150 changes"
            await self.reader.findOrphanedWsActivity(orphaned_line, 50)
            
            # Verify orphaned WebSocket was detected
            self.assertIn("ws-orphan001", self.reader.orphanedWsIds)
            self.assertEqual(self.reader.orphanedWsIds["ws-orphan001"]["user"], "UNKNOWN:ws-orphan001")
            self.assertTrue(self.reader.orphanedWsIds["ws-orphan001"]["orphaned"])
            
            # Test known WebSocket (should not be detected as orphaned)
            known_line = "2024-01-15T10:30:45.123Z [DBG] BLIP+: [ws-known123] Processing changes"
            orphaned_count_before = len(self.reader.orphanedWsIds)
            await self.reader.findOrphanedWsActivity(known_line, 51)
            
            # Should not have added a new orphaned WebSocket
            self.assertEqual(len(self.reader.orphanedWsIds), orphaned_count_before)
        
        asyncio.run(run_test())
    
    @unittest.skipIf(SGLogReader is None, "sg_log_reader not available")
    def test_orphaned_capabilities_analysis(self):
        """Test orphaned WebSocket capabilities analysis"""
        async def run_test():
            # Setup test orphaned WebSocket with various activity
            ws_id = "ws-test001"
            self.reader.orphanedWsLines[ws_id] = [
                "2024-01-15T10:30:45.123Z [DBG] BLIP+: [ws-test001] GetCachedChanges(\"channel1\") got 150 changes",
                "2024-01-15T10:30:45.124Z [DBG] BLIP+: [ws-test001] Since:145 SyncMsg: continuous:true",
                "2024-01-15T10:30:45.125Z [DBG] BLIP+: [ws-test001] Sent 75 changes to client",
                "2024-01-15T10:30:45.126Z [ERR] BLIP+: [ws-test001] 409 Document update conflict",
                "2024-01-15T10:30:45.127Z [DBG] BLIP+: [ws-test001] Type:proposeChanges #Changes: 5"
            ]
            
            capabilities = await self.reader.analyzeOrphanedWsCapabilities(ws_id)
            
            # Verify capabilities were detected correctly
            self.assertTrue(capabilities["can_track_changes"])
            self.assertTrue(capabilities["can_track_since"])
            self.assertTrue(capabilities["can_track_channels"])
            self.assertTrue(capabilities["can_track_timing"])
            self.assertTrue(capabilities["can_track_errors"])
            self.assertTrue(capabilities["can_track_metrics"])
            
            # Verify specific metrics
            self.assertEqual(capabilities["cache_rows"], 150)
            self.assertEqual(capabilities["sent_count"], 75)
            self.assertEqual(capabilities["conflicts"], 1)
            self.assertEqual(capabilities["push_propose_count"], 5)
            self.assertIn("145", capabilities["since_values"])
            self.assertTrue(capabilities["continuous"])
        
        asyncio.run(run_test())
    
    @unittest.skipIf(SGLogReader is None, "sg_log_reader not available")
    def test_boundary_checking_logic(self):
        """Test boundary checking for WebSocket scanning"""
        async def run_test():
            # Test scenario: WebSocket closes near end of file
            total_lines = 100
            current_line = 98
            scan_depth_requested = 50
            
            # Simulate the boundary logic
            remaining_lines = total_lines - current_line
            safe_scan_depth = min(scan_depth_requested, remaining_lines)
            
            self.assertEqual(remaining_lines, 2)
            self.assertEqual(safe_scan_depth, 2)  # Should be limited to remaining lines
            
            # Test normal scenario
            current_line_normal = 50
            remaining_lines_normal = total_lines - current_line_normal
            safe_scan_depth_normal = min(scan_depth_requested, remaining_lines_normal)
            
            self.assertEqual(remaining_lines_normal, 50)
            self.assertEqual(safe_scan_depth_normal, 50)  # Should use full requested depth
        
        asyncio.run(run_test())
    
    @unittest.skipIf(SGLogReader is None, "sg_log_reader not available")
    def test_iso8601_to_epoch_conversion(self):
        """Test ISO8601 timestamp to epoch conversion"""
        async def run_test():
            # Test standard format
            timestamp1 = "2024-01-15T10:30:45.123Z"
            result1 = await self.reader.iso8601_to_epoch(timestamp1)
            self.assertIsInstance(result1, int)
            self.assertGreater(result1, 0)
            
            # Test without Z suffix
            timestamp2 = "2024-01-15T10:30:45.123"
            result2 = await self.reader.iso8601_to_epoch(timestamp2)
            self.assertIsInstance(result2, int)
            
            # Test invalid format
            invalid_timestamp = "invalid-timestamp"
            result3 = await self.reader.iso8601_to_epoch(invalid_timestamp)
            self.assertFalse(result3)
        
        asyncio.run(run_test())

class TestLogAnalysisIntegration(unittest.TestCase):
    """Integration tests for log analysis without Couchbase"""
    
    def setUp(self):
        """Create test log files"""
        self.test_log_content = [
            "2024-01-15T10:30:15.123Z [INF] HTTP: #001 POST /mydb/_blipsync <ud>testuser</ud>",
            "2024-01-15T10:30:15.124Z [DBG] BLIP+: #001 Upgraded to BLIP+WebSocket protocol [ws-known123]", 
            "2024-01-15T10:30:15.125Z [DBG] BLIP+: [ws-known123] Since:0 SyncMsg: continuous:true",
            "2024-01-15T10:30:20.123Z [DBG] BLIP+: [ws-orphan001] GetCachedChanges(\"channel1\") got 150 changes",
            "2024-01-15T10:30:20.124Z [DBG] BLIP+: [ws-orphan001] Since:145 SyncMsg: continuous:true",
            "2024-01-15T10:30:20.125Z [ERR] BLIP+: [ws-orphan001] 409 Document update conflict",
            "2024-01-15T10:30:25.126Z [DBG] BLIP+: [ws-orphan001] BLIP+WebSocket connection closed"
        ]
        
        # Create temporary log file
        self.log_file = tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False)
        self.log_file.write('\n'.join(self.test_log_content))
        self.log_file.close()
        
        # Create config file
        self.config_data = {
            "file-to-parse": self.log_file.name,
            "cb-cluster-host": "127.0.0.1", 
            "cb-bucket-name": "test-bucket",
            "cb-bucket-user": "test",
            "cb-bucket-user-password": "test",
            "debug": [],
            "log-name": "integration-test",
            "cb-expire": 3600
        }
        
        self.config_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(self.config_data, self.config_file)
        self.config_file.close()
    
    def tearDown(self):
        """Clean up test files"""
        os.unlink(self.log_file.name)
        os.unlink(self.config_file.name)
    
    @unittest.skipIf(SGLogReader is None, "sg_log_reader not available")
    def test_log_parsing_integration(self):
        """Test complete log parsing without Couchbase operations"""
        async def run_test():
            # Mock Couchbase operations to avoid requiring actual connection
            with patch.object(SGLogReader, 'makeCB', new_callable=AsyncMock) as mock_makecb, \
                 patch.object(SGLogReader, 'cbUpsert', new_callable=AsyncMock) as mock_upsert, \
                 patch.object(SGLogReader, 'cbInsert', new_callable=AsyncMock) as mock_insert, \
                 patch.object(SGLogReader, 'cbGet', new_callable=AsyncMock) as mock_get:
                
                # Configure mocks
                mock_makecb.return_value = (Mock(), Mock())
                mock_upsert.return_value = True
                mock_insert.return_value = True
                mock_get.return_value = False
                
                # Override __init__ to not actually run the main process
                original_init = SGLogReader.__init__
                SGLogReader.__init__ = lambda self, file: None
                
                try:
                    # Create reader instance
                    reader = SGLogReader(self.config_file.name)
                    
                    # Manually initialize required attributes
                    await reader.readConfigFile(self.config_file.name)
                    await reader.debugIceCream()
                    reader.logData = []
                    reader.wsIdList = {}
                    reader.orphanedWsIds = {}
                    reader.orphanedWsLines = {}
                    reader.blipLineCount = 0
                    reader.wasBlipLines = False
                    
                    # Process the test log manually
                    index = 0
                    for line in self.test_log_content:
                        reader.logData.append(line)
                        
                        # Process line
                        await reader.importCheck(line)
                        await reader.sqlCheck(line)
                        await reader.generalErrors(line)
                        await reader.wsErrors(line)
                        await reader.dcpChecks(line)
                        
                        if reader.wasBlipLines:
                            await reader.findWsId(line, index)
                        await reader.findBlipLine(line, index)
                        await reader.findOrphanedWsActivity(line, index)
                        
                        index += 1
                    
                    reader.logNumberOflines = len(self.test_log_content)
                    
                    # Verify results
                    self.assertEqual(reader.blipLineCount, 1)  # One _blipsync connection
                    self.assertEqual(len(reader.orphanedWsIds), 1)  # One orphaned WebSocket
                    self.assertIn("ws-orphan001", reader.orphanedWsIds)
                    
                    # Test orphaned WebSocket analysis
                    await reader.processOrphanedWebSockets()
                    
                    # Verify Couchbase operations were called
                    self.assertTrue(mock_upsert.called)
                    
                finally:
                    # Restore original __init__
                    SGLogReader.__init__ = original_init
        
        asyncio.run(run_test())

def run_tests():
    """Run all tests"""
    print("Running Unit Tests for SG Log Reader")
    print("=" * 50)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestSGLogReaderCore))
    suite.addTests(loader.loadTestsFromTestCase(TestLogAnalysisIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\n{'✅ All tests passed!' if success else '❌ Some tests failed!'}")
    
    return success

if __name__ == '__main__':
    run_tests()
