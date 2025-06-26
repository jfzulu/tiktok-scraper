#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
[CLEAN] CLEAN OUTPUT FOLDER - TikTok Profile Analyzer
================================================
Script to clean the data/Output folder and free disk space.

Version: 1.0
Author: Carnival Cruises TikTok Analyzer Team
Date: 2024

Features:
- Removes all files and folders in data/Output
- Shows detailed statistics before deleting
- Automatic execution without user confirmation
- Safe error handling
"""

import os
import sys
import shutil
import time
from datetime import datetime
from pathlib import Path


def get_folder_size(folder_path):
    """Calculate the total size of a folder in bytes."""
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(folder_path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except (OSError, FileNotFoundError):
                    pass
    except:
        pass
    return total_size


def format_size(size_bytes):
    """Convert bytes to readable format (KB, MB, GB)."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.2f} {size_names[i]}"


def count_items_in_folder(folder_path):
    """Count files and folders in a directory."""
    if not os.path.exists(folder_path):
        return 0, 0
    
    total_files = 0
    total_folders = 0
    
    try:
        for root, dirs, files in os.walk(folder_path):
            total_files += len(files)
            total_folders += len(dirs)
    except:
        pass
    
    return total_files, total_folders


def show_statistics(output_path):
    """Show detailed statistics of the folder to be cleaned."""
    print("[CHART] STATISTICS OF data/Output FOLDER:")
    print("=" * 50)
    
    if not os.path.exists(output_path):
        print("[ERROR] The data/Output folder does not exist.")
        return 0, 0, 0
    
    # Get general statistics
    total_size = get_folder_size(output_path)
    total_files, total_folders = count_items_in_folder(output_path)
    
    print(f"[FOLDER] Location: {os.path.abspath(output_path)}")
    print(f"[CHART] Total size: {format_size(total_size)}")
    print(f"[PAGE] Total files: {total_files:,}")
    print(f"[EMOJI] Total folders: {total_folders:,}")
    
    # Show existing sessions
    try:
        sessions = [d for d in os.listdir(output_path) 
                   if os.path.isdir(os.path.join(output_path, d)) and d.startswith('session_')]
        
        if sessions:
            print(f"\n[EMOJI] Sessions found ({len(sessions)}):")
            for session in sorted(sessions)[-5:]:  # Last 5 sessions
                session_path = os.path.join(output_path, session)
                session_size = get_folder_size(session_path)
                print(f"   • {session}: {format_size(session_size)}")
            
            if len(sessions) > 5:
                print(f"   ... and {len(sessions) - 5} more sessions")
    except:
        print("[WARNING]  Could not read sessions")
    
    print("=" * 50)
    return total_size, total_files, total_folders


def clean_output_folder():
    """Main function to clean the data/Output folder."""
    print("[CLEAN] CLEANING TOOL - TikTok Profile Analyzer")
    print("=" * 60)
    print("This tool will automatically delete all content in data/Output folder")
    print("to free disk space and reset the workspace.")
    print("=" * 60)
    
    # Define path to Output folder
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_path = os.path.join(base_dir, "data", "Output")
    
    # Show statistics
    total_size, total_files, total_folders = show_statistics(output_path)
    
    if total_files == 0 and total_folders == 0:
        print("\n[OK] The data/Output folder is already empty. Nothing to clean.")
        return
    
    # Proceed with cleaning automatically
    print("\n[CLEAN] Starting automatic cleanup...")
    start_time = time.time()
    
    try:
        deleted_items = 0
        
        # Delete folder content
        for item_name in os.listdir(output_path):
            item_path = os.path.join(output_path, item_name)
            
            try:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                    print(f"   [EMOJI]  Folder deleted: {item_name}")
                else:
                    os.remove(item_path)
                    print(f"   [EMOJI]  File deleted: {item_name}")
                
                deleted_items += 1
                
            except Exception as e:
                print(f"   [ERROR] Error deleting {item_name}: {e}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Show final summary
        print("\n" + "=" * 60)
        print("[OK] CLEANUP COMPLETED")
        print("=" * 60)
        print(f"[CHART] Space freed: {format_size(total_size)}")
        print(f"[PAGE] Files deleted: {total_files:,}")
        print(f"[EMOJI] Folders deleted: {total_folders:,}")
        print(f"⏱[EMOJI]  Time elapsed: {duration:.2f} seconds")
        print(f"[FOLDER] The data/Output folder is now empty and ready for new analysis")
        
    except Exception as e:
        print(f"\n[ERROR] ERROR DURING CLEANUP: {e}")
        print("The cleanup operation was not completed successfully.")
        return
    
    print("\n[PARTY] Cleanup completed successfully!")


if __name__ == "__main__":
    try:
        clean_output_folder()
    except KeyboardInterrupt:
        print("\n\n[ERROR] Operation interrupted by user (Ctrl+C)")
        print("Cleanup was not completed.")
    except Exception as e:
        print(f"\n[ERROR] UNEXPECTED ERROR: {e}")
        print("Please report this error to the development team.")
    
    print("\nPress Enter to close...")
    input() 