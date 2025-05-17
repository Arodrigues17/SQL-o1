#!/usr/bin/env bash

# SQL-o1 Execution Script with Groq API
# This script implements the instructions from the SQL-o1 GitHub README
# but uses Groq API instead of the default LLM

set -e  # Exit on error

echo "========================================================"
echo "SQL-o1 Execution Script with Groq API"
echo "========================================================"

# Check if GROQ_API_KEY is set
if [ -z "$GROQ_API_KEY" ]; then
    echo "GROQ_API_KEY environment variable is not set."
    echo "Please make sure it's defined in your .bashrc file."
    echo "You can add it by running: echo 'export GROQ_API_KEY=your-api-key' >> ~/.bashrc"
    exit 1
fi

# Function to prompt user for input with default
prompt_user() {
    local prompt_text="$1"
    local default_value="$2"
    read -p "$prompt_text [$default_value]: " var
    var="${var:-$default_value}"
    echo $var
}

# Function to check if directory exists
check_directory() {
    if [ ! -d "$1" ]; then
        echo "Directory $1 does not exist!"
        exit 1
    fi
}

# Set up working directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
cd "$SCRIPT_DIR"

# Ask for dataset choice
echo "Which dataset do you want to work with?"
echo "1) Spider"
echo "2) Bird"
DATASET_CHOICE=$(prompt_user "Enter your choice (1/2)" "1")

if [ "$DATASET_CHOICE" == "1" ]; then
    DATASET="spider"
    echo "You selected Spider dataset."
elif [ "$DATASET_CHOICE" == "2" ]; then
    DATASET="bird"
    echo "You selected Bird dataset."
else
    echo "Invalid choice. Exiting."
    exit 1
fi

# Ask for mode
echo "Which mode do you want to run?"
echo "1) Train"
echo "2) Dev"
echo "3) Test (Spider only)"
echo "4) All (Run Train, Dev, and Test sequentially)"
MODE_CHOICE=$(prompt_user "Enter your choice (1/2/3/4)" "4")

if [ "$MODE_CHOICE" == "1" ]; then
    MODE="train"
    MODES=("train")
    echo "You selected Train mode."
elif [ "$MODE_CHOICE" == "2" ]; then
    MODE="dev"
    MODES=("dev")
    echo "You selected Dev mode."
elif [ "$MODE_CHOICE" == "3" ] && [ "$DATASET" == "spider" ]; then
    MODE="test"
    MODES=("test")
    echo "You selected Test mode."
elif [ "$MODE_CHOICE" == "4" ]; then
    if [ "$DATASET" == "spider" ]; then
        MODES=("train" "dev" "test")
        MODE="all"
        echo "You selected All modes. Will run Train, Dev, and Test sequentially."
    else
        MODES=("train" "dev")
        MODE="all"
        echo "You selected All modes. Will run Train and Dev sequentially."
    fi
else
    echo "Invalid mode choice or Test mode is only available for Spider. Exiting."
    exit 1
fi

# Paths
DATA_PATH="./dataset"
OUTPUT_PATH="./dataset"

# Data Preprocessing
echo "========================================================"
echo "Preprocessing data..."
echo "========================================================"

# For Spider datasets, we need to specify a variant
if [ "$DATASET" == "spider" ]; then
    echo "Which Spider variant do you want to use?"
    echo "1) Standard Spider"
    echo "2) Spider Realistic"
    echo "3) Spider DK"
    echo "4) Spider Syn"
    VARIANT_CHOICE=$(prompt_user "Enter your choice (1/2/3/4)" "1")
    
    if [ "$VARIANT_CHOICE" == "1" ]; then
        DATASET_VARIANT="spider"
    elif [ "$VARIANT_CHOICE" == "2" ]; then
        DATASET_VARIANT="spider_real"
    elif [ "$VARIANT_CHOICE" == "3" ]; then
        DATASET_VARIANT="spider_DK"
    elif [ "$VARIANT_CHOICE" == "4" ]; then
        DATASET_VARIANT="spider_syn"
    else
        echo "Invalid variant choice. Using standard Spider."
        DATASET_VARIANT="spider"
    fi
else
    DATASET_VARIANT="$DATASET"
fi

# Run preprocessing with Groq model
echo "Running preprocessing for $DATASET_VARIANT in $MODE mode"

# Choose Groq model
echo "Which Groq model would you like to use?"
echo "1) llama-3-1-8b-instant-128k (Llama 3.1 8B Instant 128k)"
echo "2) llama-3-3-70b-versatile-128k (Llama 3.3 70B Versatile 128k)"
echo "3) mixtral-8x7b-32768 (Mixtral 8x7B)"
echo "4) gemma-7b-it (Gemma 7B)"
MODEL_CHOICE=$(prompt_user "Enter your choice (1/2/3/4)" "1")

if [ "$MODEL_CHOICE" == "1" ]; then
    GROQ_MODEL="llama-3-1-8b-instant-128k"
elif [ "$MODEL_CHOICE" == "2" ]; then
    GROQ_MODEL="llama-3-3-70b-versatile-128k"
elif [ "$MODEL_CHOICE" == "3" ]; then
    GROQ_MODEL="mixtral-8x7b-32768"
elif [ "$MODEL_CHOICE" == "4" ]; then
    GROQ_MODEL="gemma-7b-it"
else
    echo "Invalid model choice. Using llama-3-1-8b-instant-128k."
    GROQ_MODEL="llama-3-1-8b-instant-128k"
fi

export GROQ_MODEL="$GROQ_MODEL"
echo "Using Groq model: $GROQ_MODEL"

# Setup Groq API server once for all modes
API_PORT=8000
export API_PORT

# Kill any existing API server
bash kill_llm_api.sh

# Start the Groq API server
echo "========================================================"
echo "Starting Groq API server..."
echo "========================================================"
nohup python src/groq_api.py > result_groq_api.log 2>&1 &
GROQ_API_PID=$!
echo "Groq API server started with PID: $GROQ_API_PID"
echo "Waiting for API server to initialize..."
sleep 10

# Process each selected mode
for CURRENT_MODE in "${MODES[@]}"; do
    echo "========================================================"
    echo "PROCESSING MODE: $CURRENT_MODE"
    echo "========================================================"
    
    # Data Preprocessing for current mode
    echo "========================================================"
    echo "Preprocessing data for $CURRENT_MODE mode..."
    echo "========================================================"

    # Determine expected intermediate file for this mode
    if [ "$CURRENT_MODE" == "train" ]; then
        PREPROCESS_FILE="./dataset/SQL-o1_spider_train_0_psg.json"
    elif [ "$CURRENT_MODE" == "dev" ]; then
        PREPROCESS_FILE="./dataset/SQL-o1_spider_dev_0_psg.json"
    elif [ "$CURRENT_MODE" == "test" ]; then
        PREPROCESS_FILE="./dataset/SQL-o1_spider_test_0_psg.json"
    else
        PREPROCESS_FILE=""
    fi

    if [ -n "$PREPROCESS_FILE" ] && [ -f "$PREPROCESS_FILE" ]; then
        echo "Preprocessing skipped: $PREPROCESS_FILE already exists."
    else
        if [ "$CURRENT_MODE" == "train" ]; then
            python preprocess_data.py --dataset "$DATASET_VARIANT" --mode "$CURRENT_MODE" --LLM_model "$GROQ_MODEL" --PSG --data_path "$DATA_PATH" --output_path "$OUTPUT_PATH"
        else
            python preprocess_data.py --dataset "$DATASET_VARIANT" --mode "$CURRENT_MODE" --LLM_model "$GROQ_MODEL" --data_path "$DATA_PATH" --output_path "$OUTPUT_PATH"
        fi
    fi
    
    # Set output paths based on mode and dataset
    if [ "$DATASET" == "bird" ]; then
        DB_PATH="./dataset/bird/dev/dev_databases"
        DIFF_PATH="./dataset/bird/dev/dev.json"
        OUTPUT_FILE="bird_${CURRENT_MODE}.sql"
    elif [ "$DATASET" == "spider" ]; then
        if [ "$CURRENT_MODE" == "dev" ]; then
            DB_PATH="./dataset/spider/database"
            DIFF_PATH="./dataset/spider/dev.json"
            OUTPUT_FILE="spider_dev.sql"
        elif [ "$CURRENT_MODE" == "test" ]; then
            DB_PATH="./dataset/spider/test_database"
            DIFF_PATH="./dataset/spider/test.json"
            OUTPUT_FILE="spider_test.sql"
        else
            DB_PATH="./dataset/spider/database"
            DIFF_PATH="./dataset/spider/dev.json"  # No specific train validation path
            OUTPUT_FILE="spider_train.sql"
        fi
    fi
    
    # Run MCTS Exploration
    echo "========================================================"
    echo "Running MCTS Exploration for $CURRENT_MODE mode..."
    echo "========================================================"
    
    TASK_NAME="$DATASET_VARIANT"
    if [ "$CURRENT_MODE" == "test" ]; then
        TASK_NAME="${DATASET_VARIANT}_test"
    fi
    
    nohup python _run_explore.py --task_name "$TASK_NAME" > "result_mcts_groq_${TASK_NAME}_${CURRENT_MODE}.txt" 2>&1 &
    EXPLORE_PID=$!
    echo "MCTS Exploration started with PID: $EXPLORE_PID"
    
    # Wait for exploration to complete
    echo "Waiting for MCTS Exploration to complete. This might take a while..."
    wait $EXPLORE_PID
    echo "MCTS Exploration completed!"
    
    # Validate results
    echo "========================================================"
    echo "Validating results for $CURRENT_MODE mode..."
    echo "========================================================"

    # Make sure the paths exist
    check_directory "$DB_PATH"

    # Use per-mode MCTS result file for validation
    VALIDATION_JSON_PATH="./mcts_results/${TASK_NAME}_mcts_${CURRENT_MODE}.json"

    echo "Running validation with the following parameters:"
    echo "JSON Path: $VALIDATION_JSON_PATH"
    echo "DB Root Path: $DB_PATH"
    echo "Diff JSON Path: $DIFF_PATH"
    echo "Output File: $OUTPUT_FILE"

    python validation_results.py \
        --json_path "$VALIDATION_JSON_PATH" \
        --db_root_path "$DB_PATH" \
        --num_cpus 1 \
        --diff_json_path "$DIFF_PATH" \
        --output_file "$OUTPUT_FILE"

    echo "========================================================"
    echo "Completed processing mode: $CURRENT_MODE"
    echo "Results saved to: $OUTPUT_FILE"
    echo "========================================================"
done

# Clean up
echo "========================================================"
echo "Cleaning up..."
echo "========================================================"

# Kill the Groq API server
bash kill_llm_api.sh

echo "========================================================"
echo "SQL-o1 execution with Groq completed!"
echo "Results can be found in: $OUTPUT_FILE"
echo "========================================================"
