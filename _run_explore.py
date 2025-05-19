import os
import argparse
import json
from tqdm import tqdm
from reasoners.algorithm import MCTS
from reasoners.t2s.agent import AgentWorldModel, AgentConfig, visualize_mcts_save, visualize_mcts_out
from reasoners import Reasoner
import copy
import random
import numpy as np
from ordered_set import OrderedSet

random.seed(0)


def dump_json(obj, fname, indent=4, mode='w', encoding="utf8", ensure_ascii=False):
    if "b" in mode:
        encoding = None
    with open(fname, "w", encoding=encoding) as f:
        return json.dump(obj, f, indent=indent, ensure_ascii=ensure_ascii)


def log_agent(agent, file_path):
    save_dict = agent
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
    with open(file_path, 'a') as f:
        json.dump(save_dict, f)
        f.write("\n")


parser = argparse.ArgumentParser(description='Parsing the input of agents, llms and llm context length.')
parser.add_argument("--task_name", type=str, help="task_name", default="spider")  # spider
parser.add_argument("--input_file", type=str, help="Dev file", default="./")  # spider
# parser.add_argument("--output_path", type=str, help="Dev file", default="")  # spider
# parser.add_argument("--split", type=int, help="split", default=0)
args = parser.parse_args()

para_configs = {
    "mcts_iters": 1, #change back to 10
    "deapth_limit": 1, #change back to 20
    "explore_rate": 100,
    "step_topk": 1, #change back to 3
    "reflect_threshold": 50.0,
    "reward_alpha": 0.4
}


def run_text2sql():


    llm_select = f'http://localhost:8000/llm'
    llm_simulate = f'http://localhost:8000/llm'
    llm_reward = f'http://localhost:8000/llm'
    base_model = {'select': llm_select, 'simulate': llm_simulate, 'reward': llm_reward}

    # Map task_name to correct file_path
    if args.task_name.startswith("bird"):
        file_path = './dataset/SQL-o1_bird_dev_db_id_0.json'
    elif args.task_name.startswith("spider_train"):
        file_path = './dataset/SQL-o1_spider_train_0_psg.json'
    elif args.task_name.startswith("spider_test"):
        file_path = './dataset/SQL-o1_spider_test_db_id_0.json'
    elif args.task_name.startswith("spider_dev"):
        file_path = './dataset/SQL-o1_spider_dev_db_id_0.json'
    elif args.task_name == "spider_syn":
        file_path = './dataset/SQL-o1_syn_spider_db_id_0.json'
    elif args.task_name == "spider_real":
        file_path = './dataset/SQL-o1_real_spider_dev_db_id_0.json'
    elif args.task_name == "spider_DK":
        file_path = './dataset/SQL-o1_DK_spider_dev_db_id_0.json'
    elif args.task_name == "spider":
        # Use the PSG file for train mode
        if os.path.exists('./dataset/SQL-o1_spider_train_0_psg.json'):
            file_path = './dataset/SQL-o1_spider_train_0_psg.json'
        else:
            file_path = './dataset/SQL-o1_spider_dev_db_id_0.json'
    else:
        raise ValueError(f"Unknown task_name: {args.task_name}")

    sql_data = json.load(open(file_path))

    # Determine mode for output filename
    if "train" in args.task_name:
        mode = "train"
    elif "test" in args.task_name:
        mode = "test"
    else:
        mode = "dev"
    os.makedirs('mcts_results', exist_ok=True)
    save_path = os.path.join('mcts_results', f'{args.task_name}_mcts_{mode}.json')

    # os.makedirs(f'/data/vda/mcts', exist_ok=True)
    # save_path = f'/data/vda/mcts/result/{args.task_name}/{args.task_name}_mcts_llama3-8b_2.json'

    prompt = para_configs.copy()

    print(f"Starting MCTS exploration for {len(sql_data)} examples...")
    save_sql_data = []
    for idx, row in enumerate(tqdm(sql_data), 1):
        print(f"[MCTS] Processing {idx}/{len(sql_data)}: {row.get('input', row.get('question', ''))[:80]}")
        world_model = AgentWorldModel(base_model=base_model, prompt=prompt, max_steps=prompt['deapth_limit'])
        config = AgentConfig(base_model=base_model, prompt=prompt, reward_alpha=prompt['reward_alpha'])
        algorithm = MCTS(depth_limit=prompt['deapth_limit'], disable_tqdm=False, output_trace_in_each_iter=True,
                         n_iters=prompt['mcts_iters'], w_exp=prompt['explore_rate'], cum_reward=np.mean, calc_q=max)  #
        reasoner_rap = Reasoner(world_model=world_model, search_config=config, search_algo=algorithm)
        result_rap = reasoner_rap(row)
        if row.get('target', ""):
            row['target'] = row['target'][:-1] if row['target'].endswith(';;') else row['target']

        row['result_mcts'] = list(OrderedSet([( res[0], res[1][-1].state.blocks_state) for res in result_rap.trace_in_each_iter]))
        if result_rap.trace_worst[1]:
            row['result_mcts_worst'] = [(result_rap.trace_worst[0], result_rap.trace_worst[1][0][-1].blocks_state)]
        else:
            row['result_mcts_worst'] = ''

        # Add more detailed debugging about what's happening with trace and SQL generation
        print(f"[DEBUG] Processing row {idx}:")
        print(f"[DEBUG] Input question: {row.get('input', row.get('question', ''))[:100]}...")
        
        if result_rap.trace_in_each_iter:
            print(f"[DEBUG] Number of MCTS iterations with results: {len(result_rap.trace_in_each_iter)}")
        else:
            print(f"[DEBUG] No MCTS iterations produced results!")
            
        # Add more debugging for trace_worst
        if result_rap.trace_worst[1]:
            row['result_mcts_worst'] = [(result_rap.trace_worst[0], result_rap.trace_worst[1][0][-1].blocks_state)]
            print(f"[DEBUG] result_mcts_worst for row {idx}: {row['result_mcts_worst'][0][1][:50]}...")
        else:
            row['result_mcts_worst'] = ''
            print(f"[DEBUG] result_mcts_worst for row {idx} is EMPTY")

        # Add more debugging for trace
        if result_rap.trace[1]:
            row['result_mcts_best'] = [(result_rap.trace[0], result_rap.trace[1][0][-1].blocks_state)]
            print(f"[DEBUG] result_mcts_best for row {idx}: {row['result_mcts_best'][0][1][:50]}...")
        else:
            row['result_mcts_best'] = ''
            print(f"[DEBUG] result_mcts_best for row {idx} is EMPTY")
            print(f"[DEBUG] Trace structure: {type(result_rap.trace)}, contents: {result_rap.trace}")
            
        save_sql_data.append(copy.deepcopy(row))
        # Print details about the output to help debug
        print(f"[DEBUG] Saved row {idx} with SQL: {row.get('result_mcts_best', '')[:50]}...")
        dump_json(save_sql_data, save_path, indent=4)
    print(f"[MCTS] Completed {len(sql_data)} examples. Output saved to {save_path}")

    # === Write SQL predictions to .sql file ===
    # Determine output .sql file name
    sql_output_file = f"spider_train.sql" if mode == "train" else (f"spider_dev.sql" if mode == "dev" else f"spider_test.sql")
    with open(sql_output_file, "w", encoding="utf-8") as fout:
        for row in save_sql_data:
            # Try to extract the best SQL prediction
            sql = ""
            if row.get('result_mcts_best') and isinstance(row['result_mcts_best'], list) and len(row['result_mcts_best']) > 0:
                sql = row['result_mcts_best'][0][1]
            # Fallback: try worst or empty string
            elif row.get('result_mcts_worst') and isinstance(row['result_mcts_worst'], list) and len(row['result_mcts_worst']) > 0:
                sql = row['result_mcts_worst'][0][1]
            # Ensure SQL ends with semicolon
            sql = (sql or '').strip()
            if sql and not sql.endswith(';'):
                sql += ';'
            fout.write(sql + "\n")
    print(f"[MCTS] SQL predictions written to {sql_output_file}")


if __name__ == '__main__':
    run_text2sql()
