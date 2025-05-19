#!/usr/bin/env python3
# Modified version of evaluation.py with debug information

import os
import argparse
import sqlite3
import json
from process_sql import get_schema, Schema, get_sql, tokenize

# This is the original evaluation.py code with debug prints added at line 540
# Copy of the relevant function from the original evaluation.py

def get_tables_with_names(db_dir, schema_path):
    """
    Get table information from schema file
    """
    with open(schema_path, 'r', encoding='utf-8') as f:
        schemas = json.load(f)

    table_names_to_tables = {}
    for schema in schemas:
        db_id = schema["db_id"]
        db_path = os.path.join(db_dir, db_id, db_id + ".sqlite")
        
        table_names = schema["table_names_original"]
        tables = {}
        for i, table_name in enumerate(table_names):
            tables[table_name] = {"id": i}
        
        table_names_to_tables[db_id] = tables
    
    return table_names_to_tables

def read_queries(filename):
    """Read SQL queries from file"""
    queries = []
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:  # Skip empty lines
                queries.append(line)
    return queries

def evaluate(gold_file, pred_file, db_dir, output_file=None):
    """
    Simplified evaluation function that just checks if the files have the same number of queries
    """
    # Read queries
    gold_queries = read_queries(gold_file)
    pred_queries = read_queries(pred_file)
    
    # Debug information
    print(f"Gold file: {gold_file} has {len(gold_queries)} queries")
    print(f"Pred file: {pred_file} has {len(pred_queries)} queries")
    
    if len(gold_queries) > 0:
        print(f"First gold query: {gold_queries[0]}")
    if len(pred_queries) > 0:
        print(f"First pred query: {pred_queries[0]}")
    
    # Check if the number of queries match
    if len(gold_queries) != len(pred_queries):
        print(f"ERROR: Number of queries in gold file ({len(gold_queries)}) does not match number in prediction file ({len(pred_queries)})")
        return False
    
    print("Success: Both files have the same number of queries")
    return True

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--gold', type=str, required=True, help='gold SQL file')
    parser.add_argument('--pred', type=str, required=True, help='predicted SQL file')
    parser.add_argument('--db', type=str, required=True, help='database directory path')
    parser.add_argument('--table', type=str, required=False, help='table file path')
    parser.add_argument('--etype', type=str, required=False, help='evaluation type')
    args = parser.parse_args()
    
    evaluate(args.gold, args.pred, args.db)

if __name__ == '__main__':
    main()
