import webbrowser
from threading import Timer
import subprocess
import os
import sys
from app import app

frontend_process = None

def start_frontend():
    global frontend_process
    print("Starting React frontend...")
    frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend')
    
    frontend_process = subprocess.Popen(
        "npm run dev",
        shell=True,
        cwd=frontend_dir
    )

def cleanup():
    global frontend_process
    if frontend_process:
        print("Stopping React frontend...")
        try:
            if sys.platform == 'win32':
                subprocess.call(['taskkill', '/F', '/T', '/PID', str(frontend_process.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                frontend_process.terminate()
        except Exception as e:
            pass # Suppress cleanup errors to avoid noisy exit
        finally:
            frontend_process = None

def open_browser():
    """Opens the default web browser to the app's React URL."""
    print("Opening browser...")
    webbrowser.open_new('http://localhost:5173/')

if __name__ == '__main__':
    print("Starting Data Analytics App...")
    
    # Start the frontend dev server
    start_frontend()
    
    # Wait 3.5 seconds for the Flask and Vite servers to start, then open the browser
    Timer(3.5, open_browser).start()
    
    # Run the Flask app
    try:
        app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()

