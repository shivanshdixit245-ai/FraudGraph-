import os
import subprocess
import signal

def kill_port(port):
    print(f"Attempting to kill process on port {port}...")
    try:
        # Get the PID
        # output format: "  TCP    0.0.0.0:8000           0.0.0.0:0              LISTENING       12345"
        cmd = f"netstat -ano"
        result = subprocess.check_output(cmd, shell=True).decode()
        
        lines = result.splitlines()
        pids = []
        for line in lines:
            if f":{port}" in line and "LISTENING" in line:
                parts = line.split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    pids.append(pid)
        
        if not pids:
            print(f"No process found on port {port}")
            return
            
        for pid in set(pids):
            print(f"Killing PID {pid}...")
            # Use taskkill /F /PID
            os.system(f"taskkill /F /PID {pid}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    kill_port(8000)
    kill_port(8001)
    kill_port(8002)
