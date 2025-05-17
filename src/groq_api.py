#!/usr/bin/env python3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Tuple, Sequence, Optional, Dict, Any
import os
import uvicorn
import json
from groq import Groq
import numpy as np
from tqdm import tqdm

# Initialize FastAPI app
app = FastAPI()

# Get Groq API key from environment variable
groq_api_key = os.environ.get("GROQ_API_KEY")
if not groq_api_key:
    raise ValueError("GROQ_API_KEY environment variable not found. Make sure it's set in your .bashrc file.")

# Initialize Groq client
groq_client = Groq(api_key=groq_api_key)

# Default model to use (can be overridden with env var)
DEFAULT_MODEL = "llama-3-1-8b-instant-128k"  # Llama 3.1 8B Instant 128k
MODEL = os.environ.get("GROQ_MODEL", DEFAULT_MODEL)

# Request model for FastAPI
class LLMRequest(BaseModel):
    input: str
    output: Sequence[str] = []


def log_score(score):
    """Helper function to log scores in a standardized format"""
    return 100.0 + score  # Matching the format from the original implementation


def calculate_score(prompt: str, completion: str) -> float:
    """
    Calculate a score for a completion given a prompt.
    This is a simple implementation that returns the log probability estimate.
    """
    # Since Groq API doesn't directly provide token-level log probabilities,
    # we need to estimate the score based on overall quality
    
    # For now, we'll use a simplified approach where we request logprobs
    # and sum them up to get a score
    try:
        response = groq_client.completions.create(
            model=MODEL,
            prompt=f"{prompt}{completion}",
            max_tokens=0,  # We don't need additional tokens, just evaluating existing ones
            logprobs=True,
            echo=True,
            temperature=0.0
        )
        
        # Extract log probabilities
        log_probs = [choice.logprobs.token_logprobs for choice in response.choices if choice.logprobs]
        if log_probs and log_probs[0]:
            # Get log probs for the completion portion
            prompt_tokens = len(prompt)
            completion_log_probs = log_probs[0][prompt_tokens:]
            return sum(completion_log_probs)
        
        return -100.0  # Default score if we can't get log probs
    
    except Exception as e:
        print(f"Error calculating score: {e}")
        return -100.0


def score(input: str, outputs: List[str]) -> List[float]:
    """Score multiple outputs against a given input"""
    scores = []
    
    # Format the input to match the expected format in the original code
    input_prompt = f"user\n\n{input}assistant\n\n"
    
    for output in outputs:
        # Calculate score for each output
        score_value = calculate_score(input_prompt, output)
        scores.append(log_score(score_value))
    
    return scores


def beam_search(input: str) -> List[Tuple[str, float]]:
    """
    Generate multiple responses using beam search and return them with scores
    """
    try:
        # Use chat completion for better instruction following
        response = groq_client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": input}],
            temperature=0.9,
            max_tokens=1024,
            n=3,  # Generate 3 completions
        )
        
        results = []
        for i, choice in enumerate(response.choices):
            content = choice.message.content
            # Calculate a score for this completion
            score_value = calculate_score(f"user\n\n{input}assistant\n\n", content)
            results.append((content, score_value))
            print(f"Generated Text {i+1} (Score: {score_value:.4f}):\n{content}\n")
            
        return results
        
    except Exception as e:
        print(f"Error in beam search: {e}")
        return [("An error occurred during generation.", -100.0)]


@app.post("/llm")
async def llm(request: LLMRequest):
    """
    Process LLM requests, either generating new completions or scoring existing ones
    """
    try:
        if not request.output or len(request.output) == 0:
            # Generate new responses using beam search
            responses = beam_search(request.input)
            return responses
        else:
            # Score existing responses
            scores = score(request.input, request.output)
            return scores
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    port = int(os.environ.get("API_PORT", "8000"))
    host = os.environ.get("API_HOST", "localhost")
    print(f"Starting Groq API server on {host}:{port} using model: {MODEL}")
    uvicorn.run(app, host=host, port=port)
