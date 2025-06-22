# Port Configuration Changes

## Summary
Updated all port configurations to avoid conflicts with existing services (Podman containers, local services, etc.).

## Changes Made

### **Web UI Port: 5000 → 5432**

**Files Updated:**
- `src/ai_doc_gen/ui/app.py` - Flask app default port
- `launch_ui.py` - UI launcher script
- `docker-compose.yml` - Container port mapping
- `PROGRESS.md` - Documentation references
- `PHASE_4_COMPLETION_SUMMARY.md` - Documentation references
- `test_ui_integration.py` - Test script references

### **Port Usage Summary**

| Service | Port | Purpose |
|---------|------|---------|
| **AI Doc Gen Web UI** | **5432** | Main web interface |
| Neo4j HTTP | 7474 | Graph database web interface |
| Neo4j Bolt | 7687 | Graph database protocol |
| PostgreSQL | 5432 | **CONFLICT RESOLVED** - Moved to 5433 if needed |

### **Why Port 5432?**
- **Avoids common conflicts:** 5000 (Flask default), 8000 (Django), 3000 (React), 8080 (Spring Boot)
- **Less likely to be used:** 5432 is typically PostgreSQL, but we're using it for the web UI
- **Easy to remember:** Matches the year 2024 (54-32)

### **Access URLs**
- **Web UI:** http://localhost:5432
- **Docker:** http://localhost:5432 (when using docker-compose)
- **Direct:** http://localhost:5432 (when using `uv run python launch_ui.py`)

### **If PostgreSQL is Running on 5432**
If you have PostgreSQL running on port 5432 and need to change it:

```bash
# Option 1: Change PostgreSQL port
# Edit postgresql.conf and change port = 5433

# Option 2: Change AI Doc Gen port
# Edit launch_ui.py and change port=5433
```

### **Testing**
All tests pass with the new port configuration:
- ✅ Flask app loads correctly
- ✅ Pipeline integration works
- ✅ Docker compose configuration updated
- ✅ Documentation updated

### **Launch Commands**
```bash
# Direct launch
uv run python launch_ui.py

# Docker launch
docker-compose up

# Both will serve on http://localhost:5432
``` 