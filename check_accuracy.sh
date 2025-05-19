#!/usr/bin/env bash

# Script to check accuracy scores from SQL-o1 execution results

# Set up working directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
cd "$SCRIPT_DIR"

echo "========================================================"
echo "Checking SQL-o1 Evaluation Results"
echo "========================================================"

# Check for MCTS result files
echo "Checking for MCTS result files..."
if ls -la mcts_results/*.json 2>/dev/null; then
    echo "MCTS result files found."
else
    echo "No MCTS result JSON files found."
fi

# Check for SQL output files
echo "========================================================"
echo "Checking for SQL output files..."
for FILE in spider_*.sql bird_*.sql; do
    if [ -f "$FILE" ] && [ -s "$FILE" ]; then
        echo "Found SQL file: $FILE with content."
        head -n 3 "$FILE"
        echo "..."
    elif [ -f "$FILE" ]; then
        echo "Found empty SQL file: $FILE"
    fi
done

# For Spider dataset, try to evaluate
echo "========================================================"
echo "Trying to run Spider evaluation on available files..."

# Try to evaluate dev results if file exists and has content
if [ -f "spider_dev.sql" ] && [ -s "spider_dev.sql" ]; then
    echo "Evaluating spider_dev.sql against dev_gold.sql"
    python test-suite-sql-eval/evaluation.py \
        --gold ./dataset/spider/dev_gold.sql \
        --pred spider_dev.sql \
        --db ./dataset/spider/database \
        --table ./dataset/spider/tables.json \
        --etype all
else
    echo "spider_dev.sql doesn't exist or is empty, skipping evaluation."
fi

# Try to evaluate train results if file exists and has content
if [ -f "spider_train.sql" ] && [ -s "spider_train.sql" ]; then
    echo "Evaluating spider_train.sql against train_gold.sql"
    python test-suite-sql-eval/evaluation.py \
        --gold ./dataset/spider/train_gold.sql \
        --pred spider_train.sql \
        --db ./dataset/spider/database \
        --table ./dataset/spider/tables.json \
        --etype all
else
    echo "spider_train.sql doesn't exist or is empty, skipping evaluation."
fi

# Check the log files
echo "========================================================"
echo "Looking for evaluation results in log files..."

# Look for accuracy strings in result files
grep -i "accuracy" result_*.* 2>/dev/null
grep -i "exact match" result_*.* 2>/dev/null
grep -i "execution match" result_*.* 2>/dev/null

echo "========================================================"
echo "Checking complete"
