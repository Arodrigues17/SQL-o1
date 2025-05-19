#!/usr/bin/env python3
"""Simple script to check SQL files"""
import sys

def count_lines(filename):
    """Count non-empty lines in a file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines()]
            non_empty = [line for line in lines if line]
            return len(lines), len(non_empty)
    except Exception as e:
        return 0, 0

def main():
    """Main function"""
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <gold_file> <pred_file>")
        return
    
    gold_file = sys.argv[1]
    pred_file = sys.argv[2]
    
    gold_lines, gold_non_empty = count_lines(gold_file)
    pred_lines, pred_non_empty = count_lines(pred_file)
    
    print(f"Gold file: {gold_file}")
    print(f"  Total lines: {gold_lines}")
    print(f"  Non-empty lines: {gold_non_empty}")
    print(f"Pred file: {pred_file}")
    print(f"  Total lines: {pred_lines}")
    print(f"  Non-empty lines: {pred_non_empty}")
    
    if gold_lines != pred_lines:
        print("ERROR: Files have different numbers of lines")
    else:
        print("SUCCESS: Files have the same number of lines")

if __name__ == "__main__":
    main()
