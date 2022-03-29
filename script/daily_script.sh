# Run this script everyday around 0:00 - 0:05
SHELL_FOLDER=$(dirname "$(readlink -f "$0")")
cd "$SHELL_FOLDER/../"
python3.8 "./script/process_yesterday_data.py"

find logs/ -mtime +30 -name "*.log" -exec rm -rf {} \;
