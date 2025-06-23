#!/usr/bin/env python3
"""
Output Dashboard for AI Documentation Generation System

A user-friendly dashboard to view, manage, and export generated documentation results.
"""

import os
import sys
import json
import webbrowser
from pathlib import Path
from datetime import datetime
import subprocess


def get_output_directories():
    """Get all output directories with their metadata."""
    outputs_dir = Path("outputs")
    if not outputs_dir.exists():
        return []
    
    directories = []
    for output_dir in outputs_dir.iterdir():
        if output_dir.is_dir():
            # Parse directory name to extract metadata
            # Format: batch_YYYYMMDD_HHMMSS_filename
            dir_name = output_dir.name
            try:
                if dir_name.startswith("batch_"):
                    parts = dir_name.split("_", 3)  # Split into max 4 parts
                    if len(parts) >= 4:
                        date_str = parts[1]
                        time_str = parts[2]
                        filename = parts[3]
                        
                        # Parse date and time
                        date_obj = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
                        
                        # Check for output files
                        draft_md = output_dir / "draft.md"
                        gap_report = output_dir / "gap_report.md"
                        provenance = output_dir / "provenance_summary.md"
                        
                        directories.append({
                            'name': dir_name,
                            'filename': filename,
                            'date': date_obj,
                            'date_str': date_obj.strftime("%Y-%m-%d %H:%M:%S"),
                            'path': output_dir,
                            'has_draft': draft_md.exists(),
                            'has_gap_report': gap_report.exists(),
                            'has_provenance': provenance.exists(),
                            'draft_size': draft_md.stat().st_size if draft_md.exists() else 0,
                            'gap_size': gap_report.stat().st_size if gap_report.exists() else 0
                        })
            except Exception:
                # Skip directories that don't match the expected format
                continue
    
    # Sort by date (newest first)
    directories.sort(key=lambda x: x['date'], reverse=True)
    return directories


def show_output_summary():
    """Show a summary of all outputs."""
    print("📊 OUTPUT DASHBOARD")
    print("=" * 60)
    
    directories = get_output_directories()
    
    if not directories:
        print("📭 No output files found.")
        print("💡 Process some documents to see results here.")
        return
    
    print(f"📁 Found {len(directories)} processed documents:")
    print()
    
    for i, dir_info in enumerate(directories, 1):
        print(f"{i:2d}. {dir_info['filename']}")
        print(f"    📅 {dir_info['date_str']}")
        print(f"    📄 Draft: {'✅' if dir_info['has_draft'] else '❌'}")
        print(f"    🔍 Gap Report: {'✅' if dir_info['has_gap_report'] else '❌'}")
        print(f"    📋 Provenance: {'✅' if dir_info['has_provenance'] else '❌'}")
        if dir_info['has_draft']:
            size_kb = dir_info['draft_size'] / 1024
            print(f"    📏 Draft Size: {size_kb:.1f} KB")
        print()


def show_detailed_view(directory_index):
    """Show detailed view of a specific output directory."""
    directories = get_output_directories()
    
    if directory_index < 1 or directory_index > len(directories):
        print("❌ Invalid directory index.")
        return
    
    dir_info = directories[directory_index - 1]
    
    print(f"📋 DETAILED VIEW: {dir_info['filename']}")
    print("=" * 60)
    print(f"📅 Processed: {dir_info['date_str']}")
    print(f"📁 Directory: {dir_info['path']}")
    print()
    
    # Show available files
    print("📄 Available Files:")
    if dir_info['has_draft']:
        print("  ✅ draft.md - Generated documentation")
    if dir_info['has_gap_report']:
        print("  ✅ gap_report.md - Gap analysis report")
    if dir_info['has_provenance']:
        print("  ✅ provenance_summary.md - Data provenance")
    
    # Check for JSON files
    json_files = list(dir_info['path'].glob("*.json"))
    for json_file in json_files:
        print(f"  📊 {json_file.name} - Raw data")
    
    print()
    
    # Show preview of draft if available
    if dir_info['has_draft']:
        draft_file = dir_info['path'] / "draft.md"
        print("📖 DRAFT PREVIEW:")
        print("-" * 40)
        try:
            with open(draft_file, 'r') as f:
                lines = f.readlines()[:10]  # First 10 lines
                for line in lines:
                    print(line.rstrip())
            if len(lines) >= 10:
                print("... (truncated)")
        except Exception as e:
            print(f"❌ Error reading draft: {e}")
        print()


def open_output_directory(directory_index):
    """Open the output directory in file explorer."""
    directories = get_output_directories()
    
    if directory_index < 1 or directory_index > len(directories):
        print("❌ Invalid directory index.")
        return
    
    dir_info = directories[directory_index - 1]
    
    try:
        if sys.platform == "darwin":  # macOS
            subprocess.run(["open", str(dir_info['path'])])
        elif sys.platform == "win32":  # Windows
            subprocess.run(["explorer", str(dir_info['path'])])
        else:  # Linux
            subprocess.run(["xdg-open", str(dir_info['path'])])
        
        print(f"✅ Opened directory: {dir_info['path']}")
    except Exception as e:
        print(f"❌ Error opening directory: {e}")


def open_output_file(directory_index, file_type):
    """Open a specific output file."""
    directories = get_output_directories()
    
    if directory_index < 1 or directory_index > len(directories):
        print("❌ Invalid directory index.")
        return
    
    dir_info = directories[directory_index - 1]
    
    file_map = {
        'draft': 'draft.md',
        'gap': 'gap_report.md',
        'provenance': 'provenance_summary.md'
    }
    
    if file_type not in file_map:
        print("❌ Invalid file type. Use: draft, gap, or provenance")
        return
    
    file_path = dir_info['path'] / file_map[file_type]
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return
    
    try:
        if sys.platform == "darwin":  # macOS
            subprocess.run(["open", str(file_path)])
        elif sys.platform == "win32":  # Windows
            subprocess.run(["start", str(file_path)], shell=True)
        else:  # Linux
            subprocess.run(["xdg-open", str(file_path)])
        
        print(f"✅ Opened file: {file_path}")
    except Exception as e:
        print(f"❌ Error opening file: {e}")


def show_processing_log():
    """Show the processing log."""
    log_file = Path("processing_log.json")
    
    if not log_file.exists():
        print("❌ Processing log not found.")
        return
    
    try:
        with open(log_file, 'r') as f:
            log_data = json.load(f)
        
        print("📋 PROCESSING LOG")
        print("=" * 60)
        
        processed_files = log_data.get('processed_files', {})
        if not processed_files:
            print("📭 No processed files found in log.")
            return
        
        print(f"📊 Total processed files: {len(processed_files)}")
        print()
        
        for filename, info in processed_files.items():
            print(f"📄 {filename}")
            print(f"   📅 {info.get('processed_at', 'Unknown')}")
            print(f"   ⏱️  {info.get('processing_time', 0):.1f}s")
            print(f"   📊 Coverage: {info.get('coverage', 0)}%")
            print(f"   🎯 Confidence: {info.get('confidence', 0)}")
            print()
    except Exception as e:
        print(f"❌ Error reading processing log: {e}")


def main():
    """Main dashboard function."""
    while True:
        print("\n" + "=" * 60)
        print("📊 AI DOCUMENTATION GENERATION - OUTPUT DASHBOARD")
        print("=" * 60)
        
        show_output_summary()
        
        print("🔧 ACTIONS:")
        print("  [1-9]  View detailed info for output")
        print("  [o]    Open output directory")
        print("  [f]    Open specific file (draft/gap/provenance)")
        print("  [l]    Show processing log")
        print("  [r]    Refresh")
        print("  [q]    Quit")
        print()
        
        choice = input("Enter your choice: ").strip().lower()
        
        if choice == 'q':
            print("👋 Goodbye!")
            break
        elif choice == 'l':
            show_processing_log()
        elif choice == 'r':
            continue
        elif choice == 'o':
            try:
                index = int(input("Enter output number: "))
                open_output_directory(index)
            except ValueError:
                print("❌ Please enter a valid number.")
        elif choice == 'f':
            try:
                index = int(input("Enter output number: "))
                file_type = input("Enter file type (draft/gap/provenance): ").strip().lower()
                open_output_file(index, file_type)
            except ValueError:
                print("❌ Please enter a valid number.")
        elif choice.isdigit():
            try:
                index = int(choice)
                show_detailed_view(index)
            except (ValueError, IndexError):
                print("❌ Please enter a valid number.")
        else:
            print("❌ Invalid choice. Please try again.")


if __name__ == "__main__":
    main() 