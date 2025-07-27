#!/usr/bin/env python3
"""
Syntax and structure validation tests for sg_log_reader*.py
Tests that don't require external dependencies
"""

import ast
import os
import re
import sys

def test_syntax_validity():
    """Test that both Python files have valid syntax"""
    print("Testing syntax validity...")
    
    files_to_test = [
        "sg_log_reader.py",
        "sg_log_reader_optimized.py"
    ]
    
    for filename in files_to_test:
        if not os.path.exists(filename):
            print(f"❌ {filename} not found")
            continue
            
        try:
            with open(filename, 'r') as f:
                source = f.read()
            
            # Parse the AST to check for syntax errors
            ast.parse(source, filename=filename)
            print(f"✅ {filename}: Syntax valid")
            
        except SyntaxError as e:
            print(f"❌ {filename}: Syntax error at line {e.lineno}: {e.msg}")
            return False
        except Exception as e:
            print(f"❌ {filename}: Error reading file: {e}")
            return False
    
    return True

def test_class_structure():
    """Test that the work class has required methods"""
    print("\nTesting class structure...")
    
    # Common methods for both versions
    common_methods = [
        "__init__",
        "main", 
        "makeCB",
        "readConfigFile",
        "findBlipLine",
        "findWsId", 
        "findOrphanedWsActivity",
        "processOrphanedWebSockets",
        "analyzeOrphanedWsCapabilities"
    ]
    
    # Version-specific methods
    original_specific = ["openSgLogFile", "getDataPerWsId"]
    optimized_specific = ["openSgLogFileOptimized", "getDataPerWsIdOptimized"]
    
    files_to_test = [
        "sg_log_reader.py",
        "sg_log_reader_optimized.py"
    ]
    
    for filename in files_to_test:
        if not os.path.exists(filename):
            continue
            
        try:
            with open(filename, 'r') as f:
                content = f.read()
            
            # Determine which methods to check based on filename
            if "optimized" in filename:
                methods_to_check = common_methods + optimized_specific
            else:
                methods_to_check = common_methods + original_specific
            
            missing_methods = []
            for method in methods_to_check:
                # Look for async def or def
                pattern = rf'async\s+def\s+{method}\s*\(|def\s+{method}\s*\('
                if not re.search(pattern, content):
                    missing_methods.append(method)
            
            if missing_methods:
                print(f"❌ {filename}: Missing methods: {', '.join(missing_methods)}")
                return False
            else:
                print(f"✅ {filename}: All required methods present")
                
        except Exception as e:
            print(f"❌ {filename}: Error checking structure: {e}")
            return False
    
    return True

def test_orphaned_websocket_implementation():
    """Test that orphaned WebSocket functionality is properly implemented"""
    print("\nTesting orphaned WebSocket implementation...")
    
    files_to_test = [
        "sg_log_reader.py",
        "sg_log_reader_optimized.py"
    ]
    
    required_patterns = [
        r'orphanedWsIds\s*=\s*{}',  # Orphaned WebSocket tracking variables
        r'orphanedWsLines\s*=\s*{}',
        r'findOrphanedWsActivity',  # Method calls
        r'processOrphanedWebSockets',
        r'UNKNOWN:', # Orphaned user naming
        r'trackChange',  # Capability tracking flags
        r'trackSince',
        r'trackChannels'
    ]
    
    for filename in files_to_test:
        if not os.path.exists(filename):
            continue
            
        try:
            with open(filename, 'r') as f:
                content = f.read()
            
            missing_patterns = []
            for pattern in required_patterns:
                if not re.search(pattern, content):
                    missing_patterns.append(pattern)
            
            if missing_patterns:
                print(f"❌ {filename}: Missing orphaned WebSocket patterns: {missing_patterns}")
                return False
            else:
                print(f"✅ {filename}: Orphaned WebSocket implementation complete")
                
        except Exception as e:
            print(f"❌ {filename}: Error checking orphaned WebSocket implementation: {e}")
            return False
    
    return True

def test_boundary_fix_implementation():
    """Test that boundary fix is properly implemented"""
    print("\nTesting boundary fix implementation...")
    
    files_to_test = [
        "sg_log_reader.py", 
        "sg_log_reader_optimized.py"
    ]
    
    required_patterns = [
        r'remaining_lines',  # Boundary checking variables
        r'scan_depth',
        r'min\(',  # Use of min() for safe scanning
        r'end_line',  # End line calculation
    ]
    
    for filename in files_to_test:
        if not os.path.exists(filename):
            continue
            
        try:
            with open(filename, 'r') as f:
                content = f.read()
            
            found_patterns = []
            for pattern in required_patterns:
                if re.search(pattern, content):
                    found_patterns.append(pattern)
            
            if len(found_patterns) < 3:  # Should have at least 3 of the 4 patterns
                print(f"❌ {filename}: Boundary fix implementation incomplete")
                return False
            else:
                print(f"✅ {filename}: Boundary fix implementation present")
                
        except Exception as e:
            print(f"❌ {filename}: Error checking boundary fix: {e}")
            return False
    
    return True

def test_regex_patterns():
    """Test that pre-compiled regex patterns exist in optimized version"""
    print("\nTesting regex patterns...")
    
    optimized_file = "sg_log_reader_optimized.py"
    
    if not os.path.exists(optimized_file):
        print(f"❌ {optimized_file} not found")
        return False
    
    expected_patterns = [
        'WS_ID_PATTERN',
        'DB_PATTERN', 
        'USER_PATTERN',
        'CRUD_PATTERN',
        'SINCE_PATTERN'
    ]
    
    try:
        with open(optimized_file, 'r') as f:
            content = f.read()
        
        missing_patterns = []
        for pattern in expected_patterns:
            if pattern not in content:
                missing_patterns.append(pattern)
        
        if missing_patterns:
            print(f"❌ {optimized_file}: Missing regex patterns: {missing_patterns}")
            return False
        else:
            print(f"✅ {optimized_file}: All regex patterns present")
            
    except Exception as e:
        print(f"❌ {optimized_file}: Error checking regex patterns: {e}")
        return False
    
    return True

def test_async_await_usage():
    """Test that async/await is used properly"""
    print("\nTesting async/await usage...")
    
    files_to_test = [
        "sg_log_reader.py",
        "sg_log_reader_optimized.py"
    ]
    
    for filename in files_to_test:
        if not os.path.exists(filename):
            continue
            
        try:
            with open(filename, 'r') as f:
                content = f.read()
            
            # Check for async methods
            async_methods = len(re.findall(r'async\s+def', content))
            await_calls = len(re.findall(r'await\s+', content))
            
            if async_methods == 0:
                print(f"❌ {filename}: No async methods found")
                return False
            
            if await_calls == 0:
                print(f"❌ {filename}: No await calls found")
                return False
                
            print(f"✅ {filename}: {async_methods} async methods, {await_calls} await calls")
            
        except Exception as e:
            print(f"❌ {filename}: Error checking async/await: {e}")
            return False
    
    return True

def run_all_tests():
    """Run all validation tests"""
    print("SG Log Reader Syntax and Structure Validation")
    print("=" * 50)
    
    tests = [
        test_syntax_validity,
        test_class_structure,
        test_orphaned_websocket_implementation,
        test_boundary_fix_implementation,
        test_regex_patterns,
        test_async_await_usage
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("Test Summary:")
    print(f"✅ Passed: {sum(results)}")
    print(f"❌ Failed: {len(results) - sum(results)}")
    
    if all(results):
        print("\n🎉 All validation tests passed!")
        print("Both sg_log_reader*.py files are structurally sound.")
    else:
        print("\n⚠️  Some validation tests failed.")
        print("Please review the issues above.")
    
    return all(results)

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
