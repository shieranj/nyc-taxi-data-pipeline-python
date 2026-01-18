#!/bin/bash

echo "============================================="
echo "===Starting Transformation & Notifications==="
echo "============================================="

cd /workspace

LOG_FILE="logs/transformation_and_notifications.log"
REPORT_FILE="logs/report.log"
ERROR_FLAG=0

#$1 placeholder for function name during calling
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" | tee -a "$LOG_FILE"
}

python3 -m src.transformation_and_notifications >> "$LOG_FILE" 2>&1

if [ $? -ne 0 ]; then
    log_error "Transformation & Notifications pipeline failed, see log file for more info"
    ERROR_FLAG=1
else
    log_message "Transformation & Notifications pipeline completed successfully"
fi

if [ $ERROR_FLAG -eq 0 ]; then 
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Transformation & Notifications: SUCCESS" >> "$REPORT_FILE"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Transformation & Notifications: FAILED" >> "$REPORT_FILE"
fi
