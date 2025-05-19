#!/usr/bin/env python3
"""
Fix SQL output file to ensure it has the same number of lines as the gold standard.
Extract actual SQL queries from MCTS results instead of using placeholders.
"""
import os
import sys
import json

def count_lines(filename):
    """Count the number of lines in a file"""
    if not os.path.exists(filename):
        return 0
    with open(filename, 'r', encoding='utf-8') as f:
        return sum(1 for _ in f)

def fix_sql_file(gold_file, sql_file, mcts_result_file=None):
    """
    Fix SQL file to have the same number of lines as the gold standard.
    Extract actual SQL queries from MCTS results if available.
    """
    # Count lines in files
    gold_lines = count_lines(gold_file)
    sql_lines = count_lines(sql_file)
    
    print(f"Gold file: {gold_file} has {gold_lines} lines")
    print(f"SQL file: {sql_file} has {sql_lines} lines")
    
    # Try to extract SQL from MCTS results file if provided
    mcts_data = []
    valid_queries = []
    
    if mcts_result_file and os.path.exists(mcts_result_file):
        try:
            with open(mcts_result_file, 'r', encoding='utf-8') as f:
                mcts_data = json.load(f)
            print(f"Loaded {len(mcts_data)} entries from MCTS results file")
            
            # Debug the structure of the MCTS results
            if len(mcts_data) > 0:
                first_entry = mcts_data[0]
                print(f"First entry keys: {list(first_entry.keys())}")
                
                # Look for the best SQL prediction in various possible locations in the MCTS result
                for entry in mcts_data:
                    sql_query = None
                    
                    # Try different possible field names where SQL might be stored
                    if 'predicted_sql' in entry:
                        sql_query = entry['predicted_sql']
                    elif 'sql' in entry:
                        sql_query = entry['sql']
                    elif 'result_mcts_best' in entry and entry['result_mcts_best']:
                        # Different formats for result_mcts_best
                        if isinstance(entry['result_mcts_best'], list) and len(entry['result_mcts_best']) > 0:
                            # Could be a list of [score, sql] pairs
                            if isinstance(entry['result_mcts_best'][0], list) and len(entry['result_mcts_best'][0]) > 1:
                                sql_query = entry['result_mcts_best'][0][1]
                            else:
                                sql_query = str(entry['result_mcts_best'][0])
                        elif isinstance(entry['result_mcts_best'], dict) and 'sql' in entry['result_mcts_best']:
                            sql_query = entry['result_mcts_best']['sql']
                    elif 'final_prediction' in entry:
                        sql_query = entry['final_prediction']
                    
                    # Clean up and validate the SQL query
                    if sql_query and isinstance(sql_query, str):
                        sql_query = sql_query.strip()
                        if not sql_query.endswith(';'):
                            sql_query += ';'
                        valid_queries.append(sql_query)
                    else:
                        valid_queries.append("SELECT 1;")  # Default fallback
                
                print(f"Extracted {len(valid_queries)} valid SQL queries")
                if valid_queries:
                    print(f"Sample SQL queries:")
                    for q in valid_queries[:3]:
                        print(f"  {q}")
                        
        except Exception as e:
            print(f"Error processing MCTS results file: {e}")
            import traceback
            traceback.print_exc()
    
    # Generate or fix SQL file
    with open(sql_file, 'w', encoding='utf-8') as f_out:
        for i in range(gold_lines):
            # Use extracted valid query if available, otherwise use a simple SELECT statement
            if i < len(valid_queries):
                sql = valid_queries[i]
            else:
                sql = "SELECT 1;"
                
            f_out.write(f"{sql}\n")
    
    print(f"Fixed SQL file now has {count_lines(sql_file)} lines")

def main():
    """Main function"""
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <gold_file> <sql_file> [mcts_result_file]")
        sys.exit(1)
    
    gold_file = sys.argv[1]
    sql_file = sys.argv[2]
    mcts_result_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    fix_sql_file(gold_file, sql_file, mcts_result_file)

if __name__ == "__main__":
    main()
