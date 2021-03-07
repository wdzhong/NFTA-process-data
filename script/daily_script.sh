# Run this script everyday around 0:00 - 0:05
SHELL_FOLDER=$(dirname "$(readlink -f "$0")")
cd "$SHELL_FOLDER/../"
python3 "./script/process_yesterday_data.py"