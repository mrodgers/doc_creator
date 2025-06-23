#!/usr/bin/env python3
"""
Error Handler for AI Documentation Generation System

Provides user-friendly error messages and recovery suggestions for common issues.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Optional


class ErrorHandler:
    """Handles errors and provides user-friendly messages."""
    
    def __init__(self):
        self.error_messages = {
            'container_not_running': {
                'title': '🚫 Services Not Running',
                'message': 'The AI documentation system services are not running.',
                'solutions': [
                    'Run: cd ai-doc-gen && podman-compose up -d',
                    'Check if Podman is installed and running',
                    'Verify your internet connection'
                ]
            },
            'port_conflict': {
                'title': '🔌 Port Conflict',
                'message': f'Port {os.getenv("WEB_PORT", "5476")} is already in use by another application.',
                'solutions': [
                    f'Stop the existing service using port {os.getenv("WEB_PORT", "5476")}',
                    'Use a different port in docker-compose.yml',
                    f'Check what\'s running: lsof -i :{os.getenv("WEB_PORT", "5476")}'
                ]
            },
            'api_key_missing': {
                'title': '🔑 API Key Missing',
                'message': 'OpenAI API key is not configured.',
                'solutions': [
                    'Set OPENAI_API_KEY environment variable',
                    'Create a .env file with your API key',
                    'Get an API key from https://platform.openai.com'
                ]
            },
            'file_not_found': {
                'title': '📁 File Not Found',
                'message': 'The specified file or directory does not exist.',
                'solutions': [
                    'Check the file path is correct',
                    'Ensure the file exists in the expected location',
                    'Verify file permissions'
                ]
            },
            'permission_denied': {
                'title': '🚫 Permission Denied',
                'message': 'You don\'t have permission to access this file or directory.',
                'solutions': [
                    'Check file permissions: ls -la filename',
                    'Change permissions: chmod +r filename',
                    'Run with appropriate user privileges'
                ]
            },
            'pdf_extraction_failed': {
                'title': '📄 PDF Extraction Failed',
                'message': 'Unable to extract content from the PDF file.',
                'solutions': [
                    'Verify the PDF file is not corrupted',
                    'Try a different PDF file',
                    'Check if the PDF is password protected',
                    'Ensure the PDF contains readable text (not just images)'
                ]
            },
            'network_error': {
                'title': '🌐 Network Error',
                'message': 'Unable to connect to required services.',
                'solutions': [
                    'Check your internet connection',
                    'Verify firewall settings',
                    'Try again in a few minutes',
                    'Check if OpenAI services are available'
                ]
            },
            'disk_space': {
                'title': '💾 Disk Space Low',
                'message': 'Insufficient disk space for processing.',
                'solutions': [
                    'Free up disk space',
                    'Remove old output files: rm -rf outputs/*',
                    'Check available space: df -h'
                ]
            },
            'memory_error': {
                'title': '🧠 Memory Error',
                'message': 'Insufficient memory for processing large files.',
                'solutions': [
                    'Close other applications to free memory',
                    'Process smaller files',
                    'Increase system memory if possible',
                    'Restart the system'
                ]
            }
        }
    
    def handle_error(self, error_type: str, details: Optional[str] = None, context: Optional[Dict] = None):
        """Handle an error and display user-friendly information."""
        if error_type not in self.error_messages:
            # Generic error handling
            print(f"❌ An unexpected error occurred: {error_type}")
            if details:
                print(f"Details: {details}")
            return
        
        error_info = self.error_messages[error_type]
        
        print(f"\n{error_info['title']}")
        print("=" * 50)
        print(f"❌ {error_info['message']}")
        
        if details:
            print(f"\n📋 Details: {details}")
        
        if context:
            print(f"\n🔍 Context: {context}")
        
        print(f"\n💡 Solutions:")
        for i, solution in enumerate(error_info['solutions'], 1):
            print(f"   {i}. {solution}")
        
        print("\n" + "=" * 50)
    
    def check_system_health(self) -> Dict[str, bool]:
        """Check the health of the system and return status."""
        health_status = {
            'podman_installed': False,
            'containers_running': False,
            'api_key_set': False,
            'disk_space_ok': False,
            'network_ok': False
        }
        
        # Check if Podman is installed
        try:
            result = subprocess.run(['podman', '--version'], capture_output=True, text=True)
            health_status['podman_installed'] = result.returncode == 0
        except FileNotFoundError:
            pass
        
        # Check if containers are running
        try:
            result = subprocess.run(['podman', 'ps'], capture_output=True, text=True)
            if result.returncode == 0 and 'ai-doc-gen-dev' in result.stdout:
                health_status['containers_running'] = True
        except Exception:
            pass
        
        # Check if API key is set
        health_status['api_key_set'] = bool(os.getenv('OPENAI_API_KEY'))
        
        # Check disk space
        try:
            stat = os.statvfs('.')
            free_space_gb = (stat.f_frsize * stat.f_bavail) / (1024**3)
            health_status['disk_space_ok'] = free_space_gb > 1.0  # At least 1GB free
        except Exception:
            pass
        
        # Check network connectivity
        try:
            result = subprocess.run(['ping', '-c', '1', '8.8.8.8'], capture_output=True, timeout=5)
            health_status['network_ok'] = result.returncode == 0
        except Exception:
            pass
        
        return health_status
    
    def show_system_health(self):
        """Display system health status."""
        print("🏥 SYSTEM HEALTH CHECK")
        print("=" * 50)
        
        health = self.check_system_health()
        
        status_icons = {True: '✅', False: '❌'}
        
        print(f"🐳 Podman Installed: {status_icons[health['podman_installed']]}")
        print(f"🚀 Containers Running: {status_icons[health['containers_running']]}")
        print(f"🔑 API Key Set: {status_icons[health['api_key_set']]}")
        print(f"💾 Disk Space OK: {status_icons[health['disk_space_ok']]}")
        print(f"🌐 Network OK: {status_icons[health['network_ok']]}")
        
        # Show issues
        issues = []
        if not health['podman_installed']:
            issues.append('Podman not installed')
        if not health['containers_running']:
            issues.append('Containers not running')
        if not health['api_key_set']:
            issues.append('API key not configured')
        if not health['disk_space_ok']:
            issues.append('Low disk space')
        if not health['network_ok']:
            issues.append('Network connectivity issues')
        
        if issues:
            print(f"\n⚠️  Issues Found:")
            for issue in issues:
                print(f"   • {issue}")
        else:
            print(f"\n✅ All systems operational!")
        
        print("=" * 50)
    
    def suggest_fixes(self, health_status: Dict[str, bool]):
        """Suggest fixes based on health status."""
        print("\n🔧 RECOMMENDED FIXES:")
        print("-" * 30)
        
        if not health_status['podman_installed']:
            print("1. Install Podman:")
            print("   macOS: brew install podman")
            print("   Linux: sudo apt-get install podman")
            print("   Windows: Download from https://podman.io")
        
        if not health_status['containers_running']:
            print("2. Start containers:")
            print("   cd ai-doc-gen && podman-compose up -d")
        
        if not health_status['api_key_set']:
            print("3. Set API key:")
            print("   export OPENAI_API_KEY='your-key-here'")
            print("   Or create .env file with OPENAI_API_KEY=your-key-here")
        
        if not health_status['disk_space_ok']:
            print("4. Free disk space:")
            print("   rm -rf outputs/*")
            print("   rm -rf cache/*")
        
        if not health_status['network_ok']:
            print("5. Check network:")
            print("   Verify internet connection")
            print("   Check firewall settings")
        
        print("-" * 30)


def main():
    """Main function for standalone error handler."""
    handler = ErrorHandler()
    
    print("🔧 AI Documentation Generation - Error Handler")
    print("=" * 50)
    
    handler.show_system_health()
    
    health = handler.check_system_health()
    if not all(health.values()):
        handler.suggest_fixes(health)
    
    print("\n📋 Common Error Types:")
    print("  [1] Container not running")
    print("  [2] Port conflict")
    print("  [3] API key missing")
    print("  [4] File not found")
    print("  [5] Permission denied")
    print("  [6] PDF extraction failed")
    print("  [7] Network error")
    print("  [8] Disk space low")
    print("  [9] Memory error")
    print("  [q] Quit")
    
    while True:
        choice = input("\nSelect error type (or 'q' to quit): ").strip()
        
        if choice == 'q':
            break
        elif choice.isdigit() and 1 <= int(choice) <= 9:
            error_types = [
                'container_not_running',
                'port_conflict', 
                'api_key_missing',
                'file_not_found',
                'permission_denied',
                'pdf_extraction_failed',
                'network_error',
                'disk_space',
                'memory_error'
            ]
            error_type = error_types[int(choice) - 1]
            handler.handle_error(error_type)
        else:
            print("❌ Invalid choice. Please try again.")


if __name__ == "__main__":
    main() 