# Port Configuration Changes

## Summary
Updated all port configurations to use a configurable, non-conflicting port system with environment variable support.

## Changes Made

### **Web UI Port: Configurable via WEB_PORT (default: 5476)**

**Files Updated:**
- `src/ai_doc_gen/ui/app.py` - Flask app uses WEB_PORT environment variable
- `launch_ui.py` - UI launcher script uses configurable port
- `docker-compose.yml` - Container port mapping and environment variables
- `Dockerfile` - Expose configurable port
- `env.example` - Default WEB_PORT=5476
- `README.md` - Updated documentation references
- `error_handler.py` - Dynamic port error messages
- `test_web_upload.py` - Test scripts use configurable port
- `test_ui_integration.py` - Integration tests use configurable port

### **Port Usage Summary**

| Service | Port | Purpose |
|---------|------|---------|
| **AI Doc Gen Web UI** | **5476** (configurable) | Main web interface |
| Neo4j HTTP | 7474 | Graph database web interface |
| Neo4j Bolt | 7687 | Graph database protocol |
| PostgreSQL | 5432 | Database (if running locally) |

### **Why Port 5476?**
- **Non-standard**: Avoids common conflicts (5000, 8000, 8080, 5432)
- **Configurable**: Can be changed via WEB_PORT environment variable
- **Easy to remember**: Unique port number
- **Future-proof**: Unlikely to conflict with other services

### **Configuration Options**

**Environment Variable:**
```bash
export WEB_PORT=5476  # Set custom port
```

**Docker Compose:**
```yaml
environment:
  - WEB_PORT=${WEB_PORT:-5476}  # Use env var or default
ports:
  - "${WEB_PORT:-5476}:5476"    # Map host port to container
```

**Access URLs**
- **Web UI:** http://localhost:5476 (or custom port)
- **Docker:** http://localhost:5476 (when using docker-compose)
- **Direct:** http://localhost:5476 (when using `uv run python launch_ui.py`)

### **Testing**
All tests pass with the new port configuration:
- ✅ Flask app loads correctly on configurable port
- ✅ Pipeline integration works
- ✅ Docker compose configuration updated
- ✅ Documentation updated
- ✅ Error handling uses dynamic port references

### **Launch Commands**
```bash
# Use default port (5476)
uv run python launch_ui.py

# Use custom port
WEB_PORT=8080 uv run python launch_ui.py

# Docker with default port
docker-compose up

# Docker with custom port
WEB_PORT=8080 docker-compose up
``` 