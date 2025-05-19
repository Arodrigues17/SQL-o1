#!/usr/bin/env python3
"""
Script to inspect and diagnose MCTS results files to understand their structure.
This helps in fixing the SQL prediction issues.
"""
import json
import sys
import os

def inspect_mcts_results(mcts_results_file):
    """
    Analyze the MCTS results file to understand its structure and content.
    
    Args:
        mcts_results_file: Path to the MCTS results JSON file
    """
    try:
        with open(mcts_results_file, 'r') as f:
            mcts_results = json.load(f)
        
        # Print basic information about the file
        print(f"Type of MCTS results: {type(mcts_results)}")
        if isinstance(mcts_results, list):
            print(f"Number of entries: {len(mcts_results)}")
        elif isinstance(mcts_results, dict):
            print(f"Keys in top-level dictionary: {list(mcts_results.keys())}")
            
        # Analyze the first few entries to understand structure
        if isinstance(mcts_results, list) and len(mcts_results) > 0:
            print("\nAnalyzing first entry:")
            first_entry = mcts_results[0]
            print(f"Keys: {list(first_entry.keys())}")
            
            # Check for common fields where SQL predictions might be stored
            sql_field_candidates = [
                'predicted_sql', 'sql', 'result_mcts_best', 'final_prediction',
                'best_result', 'query', 'output'
            ]
            
            for field in sql_field_candidates:
                if field in first_entry:
                    print(f"\nFound '{field}' in entry:")
                    print(f"Type: {type(first_entry[field])}")
                    print(f"Value: {first_entry[field]}")
                    
                    # For nested structures, dig deeper
                    if isinstance(first_entry[field], dict):
                        print(f"Dictionary keys: {list(first_entry[field].keys())}")
                    elif isinstance(first_entry[field], list) and len(first_entry[field]) > 0:
                        print(f"List length: {len(first_entry[field])}")
                        print(f"First item type: {type(first_entry[field][0])}")
                        print(f"First item value: {first_entry[field][0]}")
            
            # Count entries with actual SQL queries
            sql_count = 0
            empty_count = 0
            placeholder_count = 0
            
            for entry in mcts_results:
                has_sql = False
                for field in sql_field_candidates:
                    if field in entry and entry[field]:
                        # Very simple heuristic: check if the string contains "SELECT"
                        if isinstance(entry[field], str) and "SELECT" in entry[field].upper():
                            sql_count += 1
                            has_sql = True
                            break
                        elif isinstance(entry[field], list) and len(entry[field]) > 0:
                            # Check first item if it's a string
                            if isinstance(entry[field][0], str) and "SELECT" in entry[field][0].upper():
                                sql_count += 1
                                has_sql = True
                                break
                            # If it's a list like [score, sql]
                            elif isinstance(entry[field][0], list) and len(entry[field][0]) > 1:
                                if isinstance(entry[field][0][1], str) and "SELECT" in entry[field][0][1].upper():
                                    sql_count += 1
                                    has_sql = True
                                    break
                
                if not has_sql:
                    if any(isinstance(entry.get(field), str) and entry.get(field) == "done;" 
                           for field in sql_field_candidates):
                        placeholder_count += 1
                    else:
                        empty_count += 1
            
            print(f"\nSQL query statistics:")
            print(f"Entries with SQL queries: {sql_count}")
            print(f"Entries with 'done;' placeholder: {placeholder_count}")
            print(f"Entries with no SQL: {empty_count}")
            
    except Exception as e:
        print(f"Error analyzing MCTS results: {e}")
        import traceback
        traceback.print_exc()

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <mcts_results_file>")
        sys.exit(1)
    
    mcts_results_file = sys.argv[1]
    if not os.path.exists(mcts_results_file):
        print(f"Error: File {mcts_results_file} does not exist")
        sys.exit(1)
        
    inspect_mcts_results(mcts_results_file)

if __name__ == "__main__":
    main()
