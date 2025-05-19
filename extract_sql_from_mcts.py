# extract_sql_from_mcts.py
import json

mode = "train"  # or "dev" or "test"
mcts_json = f"mcts_results/spider_train_mcts_train.json"  # adjust as needed
sql_output_file = f"spider_train.sql" if mode == "train" else (f"spider_dev.sql" if mode == "dev" else f"spider_test.sql")

with open(mcts_json, "r", encoding="utf-8") as fin:
    save_sql_data = json.load(fin)

with open(sql_output_file, "w", encoding="utf-8") as fout:
    for row in save_sql_data:
        sql = ""
        if row.get('result_mcts_best') and isinstance(row['result_mcts_best'], list) and len(row['result_mcts_best']) > 0:
            sql = row['result_mcts_best'][0][1]
        elif row.get('result_mcts_worst') and isinstance(row['result_mcts_worst'], list) and len(row['result_mcts_worst']) > 0:
            sql = row['result_mcts_worst'][0][1]
        sql = (sql or '').strip()
        if sql and not sql.endswith(';'):
            sql += ';'
        fout.write(sql + "\n")
print(f"SQL predictions written to {sql_output_file}")