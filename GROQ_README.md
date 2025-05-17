# SQL-o1 with Groq API Integration

This is a custom implementation of the SQL-o1 system that uses Groq's API instead of the default LLM implementation.

## Requirements

1. You must have a Groq API key saved in your `.bashrc` file as `GROQ_API_KEY`.
2. Python 3.11+ is recommended for compatibility with all dependencies.

## Setup

Make sure your Groq API key is set in your `.bashrc` file:

```bash
echo 'export GROQ_API_KEY=your-api-key' >> ~/.bashrc
source ~/.bashrc
```

## Available Models

The script allows you to choose between the following Groq models:

1. `llama-3-1-8b-instant-128k` (Llama 3.1 8B Instant 128k)
2. `llama-3-3-70b-versatile-128k` (Llama 3.3 70B Versatile 128k)
3. `mixtral-8x7b-32768` (Mixtral 8x7B)
4. `gemma-7b-it` (Gemma 7B)

## Running the Script

To run the SQL-o1 system with Groq integration:

```bash
cd /home/anthony/dev/Big-Data/Final_Project/SQL-o1
./run_with_groq.sh
```

The script will guide you through the following choices:
1. Dataset selection (Spider or Bird)
2. Mode selection (Train, Dev, Test, or All)
3. Spider dataset variant (if applicable)
4. Groq model selection

When selecting "All" for the mode, the script will run through Train, Dev, and Test modes sequentially (or just Train and Dev for Bird dataset).

## Implementation Details

This implementation replaces the built-in LLM API with a custom Groq API implementation:

- `src/groq_api.py`: The main API server that connects to Groq
- `run_with_groq.sh`: The main script that executes all necessary steps

The implementation maintains compatibility with the original code while using Groq's API for language model functions.

## How It Works

The script performs the following operations:

1. Checks for Groq API key in the environment
2. Installs necessary dependencies
3. Preprocesses the selected dataset
4. Starts the Groq API server
5. Runs MCTS exploration using the Groq model
6. Validates the results
7. Cleans up by stopping the API server

## Output

Results will be saved in the specified output file (e.g., `spider_dev.sql` or `bird_dev.sql`).

## Troubleshooting

If you encounter any issues:

1. Make sure your Groq API key is correctly set
2. Check the log files (e.g., `result_groq_api.log`, `result_mcts_groq_*.txt`)
3. Make sure all paths specified in the script exist
4. Ensure you have internet connectivity for API calls to Groq
