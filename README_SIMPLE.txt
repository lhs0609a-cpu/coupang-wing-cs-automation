========================================================================
  SIMPLE SOLUTION - Coupang Wing CS Launcher
========================================================================

PROBLEM:
--------
The batch files with Korean characters (최종실행파일.bat) have encoding
issues on some Windows systems.

SOLUTION:
---------
Use the new English-named files instead!

FILES CREATED:
--------------
1. run_server.py  (Main launcher script)
2. START.bat      (Simple batch file - DOUBLE CLICK THIS!)

HOW TO USE:
-----------
Simply DOUBLE CLICK on: START.bat

This will automatically:
- Find available ports
- Start backend server
- Verify backend connection (auto-retry up to 30 times)
- Start frontend server
- Verify frontend connection (auto-retry up to 20 times)
- Retry with different ports if connection fails (up to 10 times)
- Open web browser automatically

FEATURES:
---------
✓ Progress bars for port scanning
✓ Progress bars for connection attempts
✓ Detailed logging with timestamps
✓ Automatic port detection
✓ Automatic retry on failure
✓ Browser auto-launch
✓ Statistics display

AFTER RUNNING:
--------------
You will see something like:

═════════════════════════════════════════════════════════════
  🎉 SUCCESS! ALL SYSTEMS OPERATIONAL!
═════════════════════════════════════════════════════════════

  📊 Server Information:
  ├─ Frontend:  http://localhost:3002
  ├─ Backend:   http://localhost:8002
  └─ API Docs:  http://localhost:8002/docs

TO STOP SERVERS:
----------------
1. Press Ctrl+C in the backend console window
2. Press Ctrl+C in the frontend console window

REQUIREMENTS:
-------------
- Python installed and in PATH
- backend/ and frontend/ folders in same directory
- venv/ virtual environment set up
- Node.js and npm installed

TROUBLESHOOTING:
----------------
Q: Nothing happens when I double click START.bat
A: Make sure Python is installed and in your PATH

Q: "python not found" error
A: Install Python and add it to system PATH

Q: Servers fail to start
A: Check that backend/ and frontend/ directories exist

========================================================================
