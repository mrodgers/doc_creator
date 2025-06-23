#!/usr/bin/env python3
"""
AI Documentation Generation System Launcher

A user-friendly launcher that provides easy access to the web interface
and batch processing system.
"""

import os
import sys
import subprocess
import webbrowser
from pathlib import Path


def run_command(cmd, capture_output=True):
    """Run a command and return the result."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=capture_output, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def check_container_status():
    """Check if the required containers are running."""
    print("🔍 Checking container status...")
    
    # Check if containers exist and are running
    success, output, error = run_command("podman ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'")
    
    if not success:
        print("❌ Error checking containers. Is Podman installed and running?")
        return False, {}
    
    containers = {}
    lines = output.strip().split('\n')[1:]  # Skip header
    
    for line in lines:
        if line.strip():
            # Split by multiple spaces and filter out empty parts
            parts = [part for part in line.split('  ') if part.strip()]
            if len(parts) >= 2:
                name = parts[0].strip()
                status = parts[1].strip()
                ports = parts[2].strip() if len(parts) > 2 else ""
                
                # Check for various running states including "starting"
                running = any(state in status for state in ['Up', 'running', 'starting'])
                containers[name] = {
                    'status': status,
                    'ports': ports,
                    'running': running
                }
    
    return True, containers


def open_web_interface():
    """Open the web interface in the default browser."""
    print("🌐 Opening web interface...")
    
    # Try to open the web UI
    try:
        webbrowser.open('http://localhost:5432')
        print("✅ Web interface opened in your browser!")
        return True
    except Exception as e:
        print(f"❌ Could not open browser automatically: {e}")
        print("📋 Please manually open: http://localhost:5432")
        return False


def show_status(containers):
    """Display current system status."""
    print("\n" + "="*60)
    print("🎯 AI DOCUMENTATION GENERATION SYSTEM STATUS")
    print("="*60)
    
    # Web UI Status
    ai_doc_gen = containers.get('ai-doc-gen-dev', {})
    if ai_doc_gen.get('running', False):
        print("✅ Web UI: Running at http://localhost:5432")
    else:
        print("❌ Web UI: Not running")
    
    # Neo4j Status
    neo4j = containers.get('ai-doc-gen-neo4j', {})
    if neo4j.get('running', False):
        print("✅ Neo4j: Running at http://localhost:7474")
    else:
        print("❌ Neo4j: Not running")
    
    print("\n📁 File Processing:")
    print("   • Upload files to: uploads/pending/")
    print("   • Processed files: uploads/processed/")
    print("   • Output results: outputs/")
    
    print("\n🔧 Management Commands:")
    print("   • Stop services: cd ai-doc-gen && podman-compose down")
    print("   • View logs: cd ai-doc-gen && podman-compose logs")
    print("   • Restart: cd ai-doc-gen && podman-compose restart")
    
    print("="*60)


def show_quick_start():
    """Show quick start instructions."""
    print("\n🚀 QUICK START GUIDE")
    print("-" * 40)
    print("1. Use the web interface at http://localhost:5432")
    print("2. Drag and drop PDF files to upload")
    print("3. Monitor processing in real-time")
    print("4. View results and analytics")
    print("\n📚 Alternative: Upload files to 'uploads/pending/' for batch processing")
    print("\n📊 View Results: python output_dashboard.py")


def main():
    """Main launcher function."""
    print("🎯 AI Documentation Generation System Launcher")
    print("=" * 50)
    
    # Check if containers are running
    success, containers = check_container_status()
    if not success:
        print("❌ Failed to check container status")
        return 1
    
    # Check if services are running
    ai_doc_gen_running = containers.get('ai-doc-gen-dev', {}).get('running', False)
    neo4j_running = containers.get('ai-doc-gen-neo4j', {}).get('running', False)
    
    if not ai_doc_gen_running:
        print("❌ Web UI is not running.")
        print("💡 To start the services, run: cd ai-doc-gen && podman-compose up -d")
        return 1
    
    # Show current status
    show_status(containers)
    
    # Ask if user wants to open web interface
    response = input("\nWould you like to open the web interface? (y/n): ").lower().strip()
    if response in ['y', 'yes']:
        open_web_interface()
    
    # Ask if user wants to view outputs
    response = input("\nWould you like to view output results? (y/n): ").lower().strip()
    if response in ['y', 'yes']:
        print("🚀 Launching output dashboard...")
        subprocess.run([sys.executable, "output_dashboard.py"])
    
    # Show quick start guide
    show_quick_start()
    
    print("\n✅ System is ready! Happy documenting! 🎉")
    return 0


if __name__ == "__main__":
    sys.exit(main()) 