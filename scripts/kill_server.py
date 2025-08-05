#!/usr/bin/env python3
"""
Kill any hanging PaperQA2 server processes.
"""

import os
import subprocess
import sys

def kill_processes_on_ports(ports):
    """Kill processes running on specified ports."""
    killed_any = False
    
    for port in ports:
        try:
            # Find processes on this port
            result = subprocess.run(
                ["lsof", "-ti:" + str(port)], 
                capture_output=True, 
                text=True
            )
            
            if result.returncode == 0 and result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                print(f"🔍 Found {len(pids)} process(es) on port {port}")
                
                for pid in pids:
                    if pid.strip():
                        try:
                            subprocess.run(["kill", "-9", pid.strip()], check=True)
                            print(f"✅ Killed process {pid} on port {port}")
                            killed_any = True
                        except subprocess.CalledProcessError:
                            print(f"❌ Failed to kill process {pid}")
            else:
                print(f"✅ No processes found on port {port}")
                
        except FileNotFoundError:
            print("❌ lsof command not found")
            return False
        except Exception as e:
            print(f"❌ Error checking port {port}: {e}")
    
    return killed_any

def main():
    """Kill PaperQA2 server processes."""
    print("🔪 PaperQA2 Server Process Killer")
    print("=" * 35)
    
    # Ports that PaperQA2 might use
    ports = [7860, 7861, 7862, 7863, 7864]
    
    killed_any = kill_processes_on_ports(ports)
    
    if killed_any:
        print("\n🎉 Killed hanging processes. You can now start the server.")
    else:
        print("\n✅ No hanging processes found. Server should be available.")
    
    print("\n💡 To start server: make ui")

if __name__ == "__main__":
    main()