#!/usr/bin/env python3
"""
Benchmark script to compare performance between original and optimized versions
"""

import time
import psutil
import os
import subprocess
import sys
import json
from pathlib import Path

class MemoryMonitor:
    def __init__(self, pid):
        self.process = psutil.Process(pid)
        self.max_memory = 0
        self.max_memory_mb = 0
    
    def update(self):
        try:
            memory_info = self.process.memory_info()
            current_memory = memory_info.rss  # Resident Set Size
            if current_memory > self.max_memory:
                self.max_memory = current_memory
                self.max_memory_mb = current_memory / (1024 * 1024)
            return current_memory / (1024 * 1024)  # Convert to MB
        except psutil.NoSuchProcess:
            return 0

def run_benchmark(script_name, config_file):
    """Run a script and monitor its performance"""
    print(f"\n{'='*50}")
    print(f"Benchmarking: {script_name}")
    print(f"{'='*50}")
    
    start_time = time.time()
    
    # Start the process
    process = subprocess.Popen(
        [sys.executable, script_name, config_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Monitor memory usage
    monitor = MemoryMonitor(process.pid)
    memory_samples = []
    
    # Poll for memory usage every 0.5 seconds
    while process.poll() is None:
        current_memory = monitor.update()
        memory_samples.append(current_memory)
        time.sleep(0.5)
    
    # Get final results
    stdout, stderr = process.communicate()
    end_time = time.time()
    
    execution_time = end_time - start_time
    max_memory = monitor.max_memory_mb
    avg_memory = sum(memory_samples) / len(memory_samples) if memory_samples else 0
    
    # Print results
    print(f"Execution Time: {execution_time:.2f} seconds")
    print(f"Max Memory Usage: {max_memory:.2f} MB")
    print(f"Average Memory Usage: {avg_memory:.2f} MB")
    print(f"Exit Code: {process.returncode}")
    
    if process.returncode != 0:
        print(f"STDERR: {stderr}")
    
    if stdout:
        # Show last few lines of output
        lines = stdout.strip().split('\n')
        print("Last few lines of output:")
        for line in lines[-5:]:
            print(f"  {line}")
    
    return {
        'execution_time': execution_time,
        'max_memory_mb': max_memory,
        'avg_memory_mb': avg_memory,
        'exit_code': process.returncode,
        'output_lines': len(stdout.split('\n')) if stdout else 0
    }

def create_test_config():
    """Create a test configuration file"""
    config = {
        "file-to-parse": "test_log.log",
        "cb-cluster-host": "127.0.0.1",
        "cb-bucket-name": "sg-log-reader-test",
        "cb-bucket-user": "Administrator",
        "cb-bucket-user-password": "fujiofujio",
        "debug": [],
        "log-name": "benchmark-test",
        "cb-expire": 3600
    }
    
    with open("benchmark_config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    return "benchmark_config.json"

def create_test_log(size_mb=10):
    """Create a test log file of specified size"""
    sample_lines = [
        '2024-01-15T10:30:45.123Z [INF] HTTP: #001 POST /db/_blipsync <ud>user1</ud>',
        '2024-01-15T10:30:45.124Z [DBG] BLIP+: #001 Upgraded to BLIP+WebSocket protocol',
        '2024-01-15T10:30:45.125Z [DBG] HTTP: #001 Response: 200 OK',
        '2024-01-15T10:30:45.126Z [DBG] DCP: GetCachedChanges("channel1") got 150 changes',
        '2024-01-15T10:30:45.127Z [WRN] Import: Error processing document: timeout',
        '2024-01-15T10:30:45.128Z [ERR] Query: N1QL query failed: syntax error',
        '2024-01-15T10:30:45.129Z [DBG] WS: [ws-123] BLIP+WebSocket connection closed',
    ]
    
    target_size = size_mb * 1024 * 1024  # Convert to bytes
    current_size = 0
    
    with open("test_log.log", "w") as f:
        line_index = 0
        while current_size < target_size:
            line = sample_lines[line_index % len(sample_lines)]
            # Vary timestamps
            timestamp = f'2024-01-15T{10 + (line_index // 1000) % 14}:{(line_index // 60) % 60:02d}:{line_index % 60:02d}.{line_index % 1000:03d}Z'
            modified_line = timestamp + line[24:] + f" #{line_index}\n"
            f.write(modified_line)
            current_size += len(modified_line)
            line_index += 1
    
    print(f"Created test log file: test_log.log ({current_size / (1024*1024):.1f} MB)")
    return "test_log.log"

def main():
    print("SG Log Reader Performance Benchmark")
    print("====================================")
    
    # Check if scripts exist
    original_script = "sg_log_reader.py"
    optimized_script = "sg_log_reader_optimized.py"
    
    if not os.path.exists(original_script):
        print(f"Error: {original_script} not found")
        return
    
    if not os.path.exists(optimized_script):
        print(f"Error: {optimized_script} not found")
        return
    
    # Create test files
    print("Setting up test environment...")
    config_file = create_test_config()
    
    # Ask user for test log size
    try:
        size_mb = int(input("Enter test log file size in MB (default 10): ") or "10")
    except ValueError:
        size_mb = 10
    
    log_file = create_test_log(size_mb)
    
    # Run benchmarks
    print(f"\nRunning benchmarks with {size_mb}MB test file...")
    
    # Benchmark original version
    try:
        original_results = run_benchmark(original_script, config_file)
    except Exception as e:
        print(f"Error running original script: {e}")
        original_results = None
    
    # Benchmark optimized version  
    try:
        optimized_results = run_benchmark(optimized_script, config_file)
    except Exception as e:
        print(f"Error running optimized script: {e}")
        optimized_results = None
    
    # Compare results
    print(f"\n{'='*60}")
    print("PERFORMANCE COMPARISON")
    print(f"{'='*60}")
    
    if original_results and optimized_results:
        print(f"{'Metric':<25} {'Original':<15} {'Optimized':<15} {'Improvement':<15}")
        print(f"{'-'*70}")
        
        # Execution time
        time_improvement = original_results['execution_time'] / optimized_results['execution_time']
        print(f"{'Execution Time':<25} {original_results['execution_time']:.2f}s{'':<8} {optimized_results['execution_time']:.2f}s{'':<8} {time_improvement:.1f}x faster")
        
        # Memory usage
        memory_improvement = original_results['max_memory_mb'] / optimized_results['max_memory_mb']
        print(f"{'Max Memory Usage':<25} {original_results['max_memory_mb']:.1f}MB{'':<7} {optimized_results['max_memory_mb']:.1f}MB{'':<7} {memory_improvement:.1f}x less")
        
        # Average memory
        avg_memory_improvement = original_results['avg_memory_mb'] / optimized_results['avg_memory_mb']
        print(f"{'Avg Memory Usage':<25} {original_results['avg_memory_mb']:.1f}MB{'':<7} {optimized_results['avg_memory_mb']:.1f}MB{'':<7} {avg_memory_improvement:.1f}x less")
        
        print(f"\n📊 SUMMARY:")
        print(f"   • Processing Speed: {time_improvement:.1f}x faster")
        print(f"   • Memory Efficiency: {memory_improvement:.1f}x less memory")
        print(f"   • File Size Tested: {size_mb}MB")
        
        if optimized_results['exit_code'] == 0 and original_results['exit_code'] == 0:
            print(f"   • ✅ Both versions completed successfully")
        else:
            print(f"   • ⚠️  Some issues detected (check exit codes)")
    
    # Cleanup
    cleanup = input("\nClean up test files? (y/n): ").lower()
    if cleanup == 'y':
        for file in [config_file, log_file]:
            if os.path.exists(file):
                os.remove(file)
                print(f"Removed: {file}")

if __name__ == "__main__":
    main()
