#!/usr/bin/env python3
"""
AI Documentation Generation Web UI Launcher

Launches the Flask web interface for the AI-assisted documentation generation system.
"""

import os
import sys
from pathlib import Path

def main():
    """Launch the web UI."""
    print("AI Documentation Generation Web UI")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("pyproject.toml").exists():
        print("Error: Please run this script from the ai-doc-gen directory")
        sys.exit(1)
    
    # Check for required environment variables
    if not os.getenv("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY not set. Some features may not work.")
        print("Set it with: export OPENAI_API_KEY='your-key-here'")
    
    # Ensure required directories exist
    Path("uploads").mkdir(exist_ok=True)
    Path("outputs").mkdir(exist_ok=True)
    
    print("\nStarting web server...")
    print("Access the UI at: http://localhost:5432")
    print("Press Ctrl+C to stop the server")
    print("\n" + "=" * 50)
    
    try:
        # Import and run the Flask app
        from ai_doc_gen.ui.app import app
        app.run(debug=True, host='0.0.0.0', port=5432)
    except KeyboardInterrupt:
        print("\n\nServer stopped by user")
    except Exception as e:
        print(f"\nError starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 