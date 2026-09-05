# filemanager/ffmpeg_check.py

import subprocess
import shutil
import sys


def check_ffmpeg():
    """Check if FFmpeg is installed and available"""
    try:
        subprocess.run(['ffmpeg', '-version'], 
                      capture_output=True, 
                      check=True)
        return True
    except Exception:
        return False


def get_ffmpeg_path():
    """Get FFmpeg installation path (cross-platform)"""
    return shutil.which('ffmpeg')


def is_ffmpeg_available():
    """Alternative: Use utils.py version if imported"""
    try:
        from filemanager.utils import is_ffmpeg_available as utils_check
        return utils_check()
    except ImportError:
        # Fallback if utils not available
        return check_ffmpeg()


if __name__ == "__main__":
    print("🔍 Checking FFmpeg installation...")
    print("-" * 40)
    
    if check_ffmpeg():
        print("✅ FFmpeg is installed!")
        path = get_ffmpeg_path()
        if path:
            print(f"📁 Path: {path}")
        else:
            print("📁 Path: Could not determine (but executable found)")
        
        # Show version
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                capture_output=True, 
                                text=True)
            version_line = result.stdout.split('\n')[0]
            print(f"📦 Version: {version_line}")
        except Exception:
            pass
    else:
        print("❌ FFmpeg is NOT installed!")
        print()
        print("📥 Installation instructions:")
        print("-" * 40)
        
        if sys.platform == 'win32':
            print("Windows:")
            print("  winget install ffmpeg")
            print("  or download from: https://ffmpeg.org/download.html")
        elif sys.platform == 'darwin':
            print("macOS:")
            print("  brew install ffmpeg")
        else:
            print("Linux:")
            print("  sudo apt install ffmpeg     # Debian/Ubuntu")
            print("  sudo dnf install ffmpeg     # Fedora")
            print("  sudo pacman -S ffmpeg       # Arch")