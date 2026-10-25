#!/usr/bin/env bash
# Nisaba one-click quick-start launcher

# Determine Python command
if command -v python3 &>/dev/null; then
    PYCMD="python3"
elif command -v python &>/dev/null; then
    PYCMD="python"
elif command -v py &>/dev/null; then
    PYCMD="py"
else
    echo "❌ Error: Python 3 was not found in PATH."
    exit 1
fi

# If invoked with 'test' argument
if [ "$1" == "test" ] || [ "$1" == "tests" ]; then
    $PYCMD -m pytest tests/ -v
    exit $?
fi

clear
echo "======================================================================"
echo "   NISABA — High-Performance Sumerian Epigraphic Computational Engine"
echo "======================================================================"
echo ""
echo "  🚀 Starting Nisaba server and launching web explorer in browser..."
echo ""
echo "     • Visual Tablet Explorer : http://127.0.0.1:8000/explorer"
echo "     • Prosopography Graph    : http://127.0.0.1:8000/api/graph/view"
echo "     • REST API / SQL Console : http://127.0.0.1:8000/docs"
echo "     • One-Page User Manual   : docs/USER_MANUAL.md"
echo ""
echo "  (Keep this console open. Press Ctrl+C to terminate the server)"
echo "======================================================================"
echo ""

# Open default browser after 2 seconds in background
(
    sleep 2
    if command -v xdg-open &>/dev/null; then
        xdg-open "http://127.0.0.1:8000/explorer"
    elif command -v open &>/dev/null; then
        open "http://127.0.0.1:8000/explorer"
    fi
) &

# Run API server
$PYCMD scripts/run_api.py --port 8000 --host 127.0.0.1
