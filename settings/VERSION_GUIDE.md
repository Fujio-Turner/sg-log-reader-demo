# Version Update Guide

This guide provides detailed instructions for updating version numbers throughout the project.

## 🎯 When to Update Versions

Use semantic versioning: **MAJOR.MINOR.PATCH**

- **MAJOR**: Breaking changes or complete rewrites (e.g., 3.0.0 → 4.0.0)
- **MINOR**: New features, significant enhancements (e.g., 3.2.0 → 3.3.0)  
- **PATCH**: Bug fixes, small improvements (e.g., 3.2.0 → 3.2.1)

## 📋 Required Version Updates

When updating the project version, you MUST update these files:

### 1. app.py
**Location**: Line 16
```python
__version__ = "X.Y.Z"
```
**Purpose**: Main Flask application version used in logs and UI

### 2. sg_log_reader.py
**Location**: Line 4
```python
__version__ = "X.Y.Z"
```
**Purpose**: Original log reader version - should match major.minor with app.py

### 3. sg_log_reader_optimized.py
**Location**: Line 4
```python
__version__ = "X.Y.Z"
```
**Purpose**: Optimized log reader version - should match major.minor with app.py

## 🤖 AI Assistant Instructions

### Version Increment Rules:
1. **ALWAYS** increment version when making significant changes
2. **KEEP VERSIONS SYNCHRONIZED** across all main Python files
3. **UPDATE ALL THREE FILES** when changing any version
4. **DOCUMENT CHANGES** in commit messages with version number

### Current Version Status (as of last update):
- `app.py`: v2.2.0 (Flask web interface)
- `sg_log_reader.py`: v2.1.0 (Original log processor) 
- `sg_log_reader_optimized.py`: v2.1.0 (Performance-optimized processor)

### Version History Guidelines:
- **v2.1.0**: Added orphaned WebSocket detection and boundary fixes
- **v2.2.0**: Enhanced Flask web interface features
- **v3.0.0**: (Future) Breaking API changes or major architecture updates

### When to Increment:
- **PATCH** (x.x.+1): Bug fixes, small optimizations, documentation updates
- **MINOR** (x.+1.0): New features like orphaned WebSocket detection, performance improvements
- **MAJOR** (+1.0.0): Breaking changes, complete rewrites, API changes

### Automatic Version Checking:
The version comment includes this hint for AI assistants:
```python
# 🤖 AI ASSISTANT HINT: Please increment this version number on every significant update/save
```

### Cross-Version Compatibility:
- Keep `sg_log_reader.py` and `sg_log_reader_optimized.py` at same version
- `app.py` can have different minor/patch versions for web-specific updates
- Major versions should align across all components