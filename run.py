import subprocess
import time
import webbrowser
import os
import sys
import requests
from urllib.parse import urlparse

def is_port_in_use(port):
    """Check if a port is already in use"""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def main():
    print("Starting Company News Analyzer...")
    
    # Check if required files exist
    required_files = ["api.py", "app.py", "utils.py", "requirements.txt"]
    for file in required_files:
        if not os.path.exists(file):
            print(f"Error: {file} not found. Please make sure all required files are present.")
            sys.exit(1)
    
    # Check if the ports are already in use
    if is_port_in_use(8000):
        print("Error: Port 8000 is already in use. Make sure no other application is using it.")
        sys.exit(1)
    
    if is_port_in_use(8501):
        print("Error: Port 8501 is already in use. Make sure no other application is using it.")
        sys.exit(1)
    
    # Check if Python dependencies are installed
    try:
        import fastapi
        import streamlit
        import pandas
        import requests
        import bs4
        import uvicorn
        from gtts import gTTS
    except ImportError as e:
        print(f"Error: Missing dependencies. Please run 'pip install -r requirements.txt' first.")
        print(f"Missing dependency: {e}")
        sys.exit(1)
    
    # Start FastAPI server in a separate process
    print("Starting FastAPI server...")
    api_process = subprocess.Popen(
        ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for the API server to start with timeout and retries
    print("Waiting for API server to start...")
    max_retries = 15
    for i in range(max_retries):
        try:
            response = requests.get("http://localhost:8000/", timeout=2)
            if response.status_code == 200:
                print("API server started successfully!")
                break
        except requests.exceptions.RequestException:
            if i < max_retries - 1:
                print(f"Attempt {i+1}/{max_retries}: API server not ready yet, waiting...")
                time.sleep(2)
            else:
                print("Error: Could not connect to API server after multiple attempts.")
                # Check if process is still running
                if api_process.poll() is None:
                    stderr_output = api_process.stderr.read()
                    api_process.terminate()
                    print(f"API process error: {stderr_output}")
                else:
                    print("API process terminated unexpectedly.")
                sys.exit(1)
    
    # Start Streamlit app in a separate process
    print("Starting Streamlit app...")
    streamlit_process = subprocess.Popen(
        ["streamlit", "run", "app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for Streamlit to start
    print("Waiting for Streamlit to start...")
    max_retries = 15
    streamlit_url = "http://localhost:8501"
    for i in range(max_retries):
        try:
            response = requests.get(streamlit_url, timeout=2)
            if response.status_code == 200:
                print("Streamlit server started successfully!")
                break
        except requests.exceptions.RequestException:
            if i < max_retries - 1:
                print(f"Attempt {i+1}/{max_retries}: Streamlit not ready yet, waiting...")
                time.sleep(2)
            else:
                print("Error: Could not connect to Streamlit after multiple attempts.")
                # Check if process is still running
                if streamlit_process.poll() is None:
                    stderr_output = streamlit_process.stderr.read()
                    streamlit_process.terminate()
                    print(f"Streamlit process error: {stderr_output}")
                else:
                    print("Streamlit process terminated unexpectedly.")
                api_process.terminate()
                sys.exit(1)
    
    # Open web browser
    print("Opening web browser...")
    webbrowser.open(streamlit_url)
    
    print("Application started. Press Ctrl+C to stop.")
    
    try:
        while True:
            # Check if either process has terminated
            api_status = api_process.poll()
            streamlit_status = streamlit_process.poll()
            
            if api_status is not None:
                print(f"API server stopped unexpectedly with exit code {api_status}")
                stderr_output = api_process.stderr.read()
                print(f"API process error: {stderr_output}")
                streamlit_process.terminate()
                break
                
            if streamlit_status is not None:
                print(f"Streamlit stopped unexpectedly with exit code {streamlit_status}")
                stderr_output = streamlit_process.stderr.read()
                print(f"Streamlit process error: {stderr_output}")
                api_process.terminate()
                break
                
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\nStopping application...")
        api_process.terminate()
        streamlit_process.terminate()
        print("Application stopped.")

if __name__ == "__main__":
    main()