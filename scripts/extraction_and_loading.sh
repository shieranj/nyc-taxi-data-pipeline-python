#!/bin/bash
mkdir -p logs data/raw data/aggregation

echo "==================================="
echo "===Starting Extraction & Loading==="
echo "==================================="

cd /workspace

LOG_FILE="logs/extraction_and_loading.log"
REPORT_FILE="logs/report.log"
ERROR_FLAG=0

#$1 placeholder for function name during calling
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" | tee -a "$LOG_FILE"
}

python3 -m src.extraction_and_loading >> "$LOG_FILE" 2>&1

if [ $? -ne 0 ]; then
    log_error "Extraction & Loading pipeline failed, see log file for more info"
    ERROR_FLAG=1
else
    log_message "Extraction & Loading pipeline completed successfully"
fi


if [ $ERROR_FLAG -eq 0 ]; then 
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Extraction & Loading: SUCCESS" >> "$REPORT_FILE"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Extraction & Loading: FAILED" >> "$REPORT_FILE"
fi
