#!/usr/bin/env python3
"""
AI Documentation Generation System Launcher

Provides an easy way to start, stop, and manage the AI documentation generation system.
"""

import os
import sys
import time
import subprocess
import webbrowser
from pathlib import Path
from typing import Optional

# Import error handler
try:
    from error_handler import ErrorHandler
except ImportError:
    print("⚠️  Error handler not found. Basic error handling will be used.")
    ErrorHandler = None


class SystemLauncher:
    """Manages the AI documentation generation system."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.ai_doc_gen_dir = self.project_root / "ai-doc-gen"
        self.error_handler = ErrorHandler() if ErrorHandler else None
        
        # Check if we're in the right directory
        if not self.ai_doc_gen_dir.exists():
            print("❌ Error: ai-doc-gen directory not found!")
            print(f"Expected location: {self.ai_doc_gen_dir}")
            print("Please run this script from the project root directory.")
            sys.exit(1)
    
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met."""
        print("🔍 Checking prerequisites...")
        
        # Check if Podman is installed
        try:
            result = subprocess.run(['podman', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                if self.error_handler:
                    self.error_handler.handle_error('container_not_running', 
                                                   "Podman is not installed or not accessible")
                else:
                    print("❌ Podman is not installed or not accessible")
                    print("Please install Podman: https://podman.io/getting-started/installation")
                return False
            print(f"✅ Podman found: {result.stdout.strip()}")
        except FileNotFoundError:
            if self.error_handler:
                self.error_handler.handle_error('container_not_running', 
                                               "Podman command not found")
            else:
                print("❌ Podman command not found")
                print("Please install Podman: https://podman.io/getting-started/installation")
            return False
        
        # Check if docker-compose.yml exists
        compose_file = self.ai_doc_gen_dir / "docker-compose.yml"
        if not compose_file.exists():
            if self.error_handler:
                self.error_handler.handle_error('file_not_found', 
                                               f"docker-compose.yml not found in {self.ai_doc_gen_dir}")
            else:
                print(f"❌ docker-compose.yml not found in {self.ai_doc_gen_dir}")
            return False
        print("✅ docker-compose.yml found")
        
        # Check if API key is set
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            if self.error_handler:
                self.error_handler.handle_error('api_key_missing')
            else:
                print("⚠️  Warning: OPENAI_API_KEY environment variable not set")
                print("You'll need to set this for AI functionality to work")
        else:
            print("✅ OpenAI API key configured")
        
        return True
    
    def check_container_status(self) -> dict:
        """Check the status of running containers."""
        try:
            result = subprocess.run(['podman', 'ps'], capture_output=True, text=True)
            if result.returncode != 0:
                return {'running': False, 'error': 'Failed to check container status'}
            
            containers = result.stdout
            neo4j_running = 'neo4j' in containers.lower()
            web_running = 'ai-doc-gen-dev' in containers
            
            return {
                'running': neo4j_running and web_running,
                'neo4j': neo4j_running,
                'web': web_running,
                'containers': containers
            }
        except Exception as e:
            return {'running': False, 'error': str(e)}
    
    def start_services(self) -> bool:
        """Start the AI documentation generation services."""
        print("🚀 Starting AI documentation generation services...")
        
        try:
            # Change to the ai-doc-gen directory
            os.chdir(self.ai_doc_gen_dir)
            
            # Start services in detached mode
            result = subprocess.run(['podman-compose', 'up', '-d'], 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                if self.error_handler:
                    self.error_handler.handle_error('container_not_running', 
                                                   f"Failed to start services: {result.stderr}")
                else:
                    print(f"❌ Failed to start services: {result.stderr}")
                return False
            
            print("✅ Services started successfully!")
            
            # Wait a moment for services to fully start
            print("⏳ Waiting for services to be ready...")
            time.sleep(5)
            
            return True
            
        except Exception as e:
            if self.error_handler:
                self.error_handler.handle_error('container_not_running', str(e))
            else:
                print(f"❌ Error starting services: {e}")
            return False
    
    def stop_services(self) -> bool:
        """Stop the AI documentation generation services."""
        print("🛑 Stopping AI documentation generation services...")
        
        try:
            os.chdir(self.ai_doc_gen_dir)
            result = subprocess.run(['podman-compose', 'down'], 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"❌ Failed to stop services: {result.stderr}")
                return False
            
            print("✅ Services stopped successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error stopping services: {e}")
            return False
    
    def open_web_ui(self):
        """Open the web UI in the default browser."""
        print("🌐 Opening web UI...")
        
        # Check if services are running
        status = self.check_container_status()
        if not status['running']:
            print("❌ Services are not running. Please start them first.")
            return False
        
        port = int(os.getenv('WEB_PORT', 5476))
        try:
            webbrowser.open(f'http://localhost:{port}')
            print(f"✅ Web UI opened in your default browser on port {port}")
            print(f"📝 If the browser didn't open automatically, go to: http://localhost:{port}")
            return True
        except Exception as e:
            print(f"❌ Failed to open browser: {e}")
            print(f"📝 Please manually open: http://localhost:{port}")
            return False
    
    def show_status(self):
        """Show the current status of the system."""
        print("📊 SYSTEM STATUS")
        print("=" * 50)
        
        status = self.check_container_status()
        
        if status.get('error'):
            print(f"❌ Error checking status: {status['error']}")
            return
        
        port = int(os.getenv('WEB_PORT', 5476))
        if status['running']:
            print("✅ All services are running")
            print(f"🌐 Web UI: http://localhost:{port}")
            print("🗄️  Neo4j: http://localhost:7474")
        else:
            print("❌ Services are not running")
            if status['neo4j']:
                print("⚠️  Neo4j is running but web service is not")
            elif status['web']:
                print("⚠️  Web service is running but Neo4j is not")
            else:
                print("💡 Run 'start' to start all services")
        
        print("=" * 50)
    
    def run_batch_processor(self):
        """Run the batch processor for document processing."""
        print("📄 Running batch processor...")
        
        batch_script = self.project_root / "batch_processor.py"
        if not batch_script.exists():
            print("❌ batch_processor.py not found!")
            return False
        
        try:
            result = subprocess.run([sys.executable, str(batch_script)], 
                                  cwd=self.project_root)
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Error running batch processor: {e}")
            return False
    
    def run_output_dashboard(self):
        """Run the output dashboard."""
        print("📊 Running output dashboard...")
        
        dashboard_script = self.project_root / "output_dashboard.py"
        if not dashboard_script.exists():
            print("❌ output_dashboard.py not found!")
            return False
        
        try:
            result = subprocess.run([sys.executable, str(dashboard_script)], 
                                  cwd=self.project_root)
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Error running output dashboard: {e}")
            return False
    
    def show_help(self):
        """Show help information."""
        print("🤖 AI Documentation Generation System")
        print("=" * 50)
        print("Available commands:")
        print("  start     - Start all services")
        print("  stop      - Stop all services")
        print("  status    - Show system status")
        print("  web       - Open web UI")
        print("  batch     - Run batch processor")
        print("  dashboard - Run output dashboard")
        print("  health    - Run system health check")
        print("  help      - Show this help")
        print("  quit      - Exit")
        print("=" * 50)
        print("📝 Quick Start:")
        print("  1. Run 'start' to start services")
        print("  2. Run 'web' to open the web UI")
        print("  3. Upload documents and generate documentation")
        print("  4. Run 'dashboard' to view results")
        print("=" * 50)


def main():
    """Main function."""
    launcher = SystemLauncher()
    
    # Check prerequisites
    if not launcher.check_prerequisites():
        print("\n❌ Prerequisites not met. Please fix the issues above and try again.")
        sys.exit(1)
    
    print("\n✅ Prerequisites check passed!")
    
    # Show initial status
    launcher.show_status()
    
    # Main command loop
    while True:
        print("\n" + "=" * 50)
        command = input("Enter command (or 'help' for options): ").strip().lower()
        
        if command in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            break
        elif command == 'help' or command == 'h':
            launcher.show_help()
        elif command == 'start':
            if launcher.start_services():
                launcher.show_status()
        elif command == 'stop':
            launcher.stop_services()
        elif command == 'status':
            launcher.show_status()
        elif command == 'web':
            launcher.open_web_ui()
        elif command == 'batch':
            launcher.run_batch_processor()
        elif command == 'dashboard':
            launcher.run_output_dashboard()
        elif command == 'health':
            if launcher.error_handler:
                launcher.error_handler.show_system_health()
                health = launcher.error_handler.check_system_health()
                if not all(health.values()):
                    launcher.error_handler.suggest_fixes(health)
            else:
                print("❌ Error handler not available")
        else:
            print("❌ Unknown command. Type 'help' for available commands.")


if __name__ == "__main__":
    main() 