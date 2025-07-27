#!/usr/bin/env python3
"""
Test script to verify project structure and organization
"""

import os
import sys
import re

def test_project_structure():
    """Test that the project follows the expected structure"""
    print("Testing Project Structure...")
    
    required_files = [
        "AGENT.md",
        "sg_log_reader.py", 
        "sg_log_reader_optimized.py",
        "app.py",
        "config.json",
        "benchmark.py"
    ]
    
    required_dirs = [
        "tests",
        "settings", 
        "docs",
        "static",
        "templates"
    ]
    
    # Test required files exist
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file} exists")
        else:
            print(f"❌ {file} missing")
            return False
    
    # Test required directories exist
    for dir in required_dirs:
        if os.path.isdir(dir):
            print(f"✅ {dir}/ directory exists")
        else:
            print(f"❌ {dir}/ directory missing")
            return False
    
    return True

def test_tests_directory():
    """Test that all test files are in tests/ directory"""
    print("\nTesting Tests Directory...")
    
    expected_tests = [
        "test_boundary_fix.py",
        "test_orphaned_websockets.py", 
        "test_sg_log_reader_unit.py",
        "test_syntax_validation.py",
        "test_project_structure.py",
        "__init__.py"
    ]
    
    tests_dir = "tests"
    if not os.path.exists(tests_dir):
        print(f"❌ {tests_dir} directory missing")
        return False
    
    files_in_tests = os.listdir(tests_dir)
    
    for test_file in expected_tests:
        if test_file in files_in_tests:
            print(f"✅ tests/{test_file} exists")
        else:
            print(f"❌ tests/{test_file} missing")
            return False
    
    # Check no test files in root
    root_files = [f for f in os.listdir('.') if f.startswith('test_') and f.endswith('.py')]
    if root_files:
        print(f"❌ Test files found in root: {root_files}")
        return False
    else:
        print("✅ No test files in root directory")
    
    return True

def test_settings_directory():
    """Test that settings directory has guide files"""
    print("\nTesting Settings Directory...")
    
    settings_dir = "settings"
    if not os.path.exists(settings_dir):
        print(f"❌ {settings_dir} directory missing")
        return False
    
    required_guides = [
        "VERSION_GUIDE.md"
    ]
    
    files_in_settings = os.listdir(settings_dir)
    
    for guide_file in required_guides:
        if guide_file in files_in_settings:
            print(f"✅ settings/{guide_file} exists")
        else:
            print(f"❌ settings/{guide_file} missing")
            return False
    
    return True

def test_version_information():
    """Test that all Python files have version information"""
    print("\nTesting Version Information...")
    
    files_to_check = [
        "sg_log_reader.py",
        "sg_log_reader_optimized.py", 
        "app.py"
    ]
    
    version_pattern = r'__version__\s*=\s*["\']([0-9]+\.[0-9]+\.[0-9]+)["\']'
    
    for file in files_to_check:
        if not os.path.exists(file):
            print(f"❌ {file} not found")
            return False
        
        with open(file, 'r') as f:
            content = f.read()
        
        match = re.search(version_pattern, content)
        if match:
            version = match.group(1)
            print(f"✅ {file}: version {version}")
        else:
            print(f"❌ {file}: no version information found")
            return False
    
    return True

def test_documentation_files():
    """Test that documentation files exist"""
    print("\nTesting Documentation Files...")
    
    doc_files = [
        "AGENT.md",
        "BOUNDARY_FIX.md",
        "ORPHANED_WEBSOCKETS.md", 
        "PERFORMANCE_IMPROVEMENTS.md",
        "TEST_SUMMARY.md",
        "README.md"
    ]
    
    for doc_file in doc_files:
        if os.path.exists(doc_file):
            print(f"✅ {doc_file} exists")
        else:
            print(f"⚠️  {doc_file} missing (optional)")
    
    return True

def run_all_structure_tests():
    """Run all project structure tests"""
    print("SG Log Reader Project Structure Validation")
    print("=" * 50)
    
    tests = [
        test_project_structure,
        test_tests_directory,
        test_settings_directory,
        test_version_information,
        test_documentation_files
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
    print("Structure Test Summary:")
    print(f"✅ Passed: {sum(results)}")
    print(f"❌ Failed: {len(results) - sum(results)}")
    
    if all(results):
        print("\n🎉 All project structure tests passed!")
        print("Project is properly organized for AI agent collaboration.")
    else:
        print("\n⚠️  Some structure tests failed.")
        print("Please review the project organization.")
    
    return all(results)

if __name__ == '__main__':
    # Change to project root directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    os.chdir(project_root)
    
    success = run_all_structure_tests()
    sys.exit(0 if success else 1)
