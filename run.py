import webbrowser
from threading import Timer
from app import app

def open_browser():
    """Opens the default web browser to the app's local URL."""
    print("Opening browser...")
    webbrowser.open_new('http://127.0.0.1:5000/')

if __name__ == '__main__':
    print("Starting Data Analytics App...")
    
    # Wait 1.5 seconds for the Flask server to start, then open the browser
    Timer(1.5, open_browser).start()
    
    # Run the Flask app
    # use_reloader=False prevents the browser from opening twice during debug mode
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
