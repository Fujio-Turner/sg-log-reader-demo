# AI Agent Project Notes

## 📋 Project Overview

**SG Log Reader Demo** is a comprehensive Sync Gateway log analysis tool that processes large log files (30MB-700MB) and extracts WebSocket connection metrics, user activity patterns, and performance data. The processed data is stored in Couchbase for analysis and visualization through a Flask web interface.

## 🏗️ Project Structure

### Core Components
- **`sg_log_reader.py`** - Original log processor (v2.1.0)
- **`sg_log_reader_optimized.py`** - Performance-optimized version (v2.1.0) 
- **`app.py`** - Flask web interface (v2.2.0)
- **`config.json`** - Configuration file with database credentials and settings

### Directory Organization

```
sg-log-reader-demo/
├── 📁 tests/              # ALL unit tests go here
│   ├── test_boundary_fix.py
│   ├── test_orphaned_websockets.py
│   ├── test_sg_log_reader_unit.py
│   ├── test_syntax_validation.py
│   └── __init__.py
├── 📁 settings/           # Guide files for AI agents
│   └── VERSION_GUIDE.md   # Version management instructions
├── 📁 docs/              # Documentation
├── 📁 static/            # Web assets
├── 📁 templates/         # Flask templates
├── 📁 workspace/         # Working files
└── Core Python files
```

### 🎯 Key Features (Latest Updates)

#### 1. **Orphaned WebSocket Detection** (v2.1.0)
- **Problem**: WebSocket connections spanning multiple log files due to rotation
- **Solution**: Detects WebSocket activity without initial `_blipsync` connection
- **Output**: Creates `UNKNOWN:{ws_id}` users with capability tracking flags
- **Files**: Both `sg_log_reader*.py` versions

#### 2. **Boundary Fix** (v2.1.0) 
- **Problem**: Index errors when WebSocket closes near end of file
- **Solution**: Safe scanning depth calculation with file boundary checking
- **Impact**: Prevents crashes on large production logs
- **Files**: Both `sg_log_reader*.py` versions

#### 3. **Performance Optimizations** (v2.1.0)
- **Memory**: Streaming processing instead of loading entire file
- **Speed**: Pre-compiled regex patterns, batch database operations
- **Scalability**: Handles 700MB+ files efficiently
- **File**: `sg_log_reader_optimized.py`

## 🤖 AI Agent Guidelines

### Testing Protocol
- **ALL TESTS** must be placed in `tests/` folder
- Run `python3 tests/test_syntax_validation.py` for comprehensive validation
- Unit tests should work without external dependencies (mock Couchbase)
- Functional tests create temporary files and clean up automatically

### Version Management
- **ALWAYS** check `settings/VERSION_GUIDE.md` before making changes
- **MUST** increment version numbers on significant updates
- **SYNC** versions across `sg_log_reader*.py` files
- Use semantic versioning: MAJOR.MINOR.PATCH

### Code Standards
- **Async/await** patterns throughout for performance
- **Error handling** with graceful degradation
- **Memory efficiency** - avoid loading large files entirely
- **Batch operations** for database interactions
- **Progress tracking** for user visibility

### File Modifications
When modifying core files:
1. **Update version numbers** (see VERSION_GUIDE.md)
2. **Run all tests** in `tests/` folder  
3. **Update documentation** if functionality changes
4. **Test with large files** (use `benchmark.py`)

## 🔧 Technical Architecture

### Data Flow
```
Log File → Stream Processing → WebSocket Detection → Metrics Analysis → Couchbase Storage → Flask UI
```

### WebSocket Processing
1. **Known WebSockets**: Have initial `_blipsync` connection
2. **Orphaned WebSockets**: Activity without initial connection
3. **Capability Analysis**: Determines what metrics are trackable
4. **Storage**: Documents with tracking flags for data reliability

### Database Schema
```json
{
  "docType": "byWsId",
  "user": "username" | "UNKNOWN:ws-id",
  "orphaned": true/false,
  "trackChange": true/false,
  "trackSince": true/false, 
  "trackChannels": true/false,
  // ... metrics and activity data
}
```

## 📊 Current Status

### Completed Features ✅
- [x] Orphaned WebSocket detection and processing
- [x] Boundary safety fixes for large files
- [x] Performance optimizations for 700MB+ files
- [x] Comprehensive unit test suite
- [x] Documentation and guides
- [x] Version management system

### Known Limitations
- **Couchbase dependency**: Real usage requires Couchbase cluster
- **Single-threaded**: Could benefit from multiprocessing for very large files
- **Memory usage**: Orphaned WebSocket lines stored in memory during processing

### Performance Benchmarks
- **Original**: 45-60 minutes for 700MB file, 1.2GB RAM
- **Optimized**: 10-15 minutes for 700MB file, 80MB RAM  
- **Improvement**: 4x faster, 15x less memory

## 🚀 Future Enhancements

### Potential Improvements
1. **Cross-log correlation**: Match orphaned WebSockets across multiple files
2. **Real-time processing**: Stream processing for live logs
3. **Parallel processing**: Multi-threaded file processing
4. **Advanced analytics**: Machine learning for anomaly detection
5. **API endpoints**: REST API for programmatic access

### Next AI Agent Tasks
1. **Flask app enhancements** (focus on `app.py`)
2. **Advanced analytics features**
3. **Performance optimizations**
4. **Additional log format support**

## 📚 Important Notes for AI Agents

### Do's ✅
- **Always** update version numbers on significant changes
- **Keep** all tests in `tests/` folder
- **Use** `settings/` guides for project standards
- **Test** with large files using provided benchmark tools
- **Document** major changes in this AGENT.md file

### Don'ts ❌
- **Never** break existing API compatibility without major version bump
- **Don't** add tests outside `tests/` folder
- **Avoid** synchronous operations in async contexts
- **Don't** load entire large files into memory
- **Never** commit credentials or secrets

### Quick Commands
```bash
# Run all tests
python3 tests/test_syntax_validation.py

# Test boundary fix
python3 tests/test_boundary_fix.py

# Test orphaned WebSocket detection  
python3 tests/test_orphaned_websockets.py

# Performance benchmark
python3 benchmark.py

# Syntax validation
python3 -m py_compile sg_log_reader*.py
```

---

**Last Updated**: v2.1.0 - Added orphaned WebSocket detection and boundary fixes
**Next Focus**: Flask app enhancements and advanced analytics
