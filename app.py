from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
import logging
from datetime import datetime
from typing import List, Dict, Any
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cot_api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ChainOfThoughtClient:
    def __init__(self, api_key: str):
        self.client = openai.Client(api_key=api_key)
        
    def _generate_cot_prompt(self, original_prompt: str) -> str:
        return f"""Please help me solve this step by step:
1. First, let's break down what we need to do
2. Then, let's solve each part
3. Finally, we'll combine everything into a final answer

Question: {original_prompt}

Let's solve this step by step:"""

    def _generate_summary_prompt(self, original_prompt: str, reasoning: str) -> str:
        return f"""Based on the following step-by-step reasoning, provide a clear, concise final answer to the original question.

Original question: {original_prompt}

Reasoning process:
{reasoning}

Final answer:"""

    def generate_response(self, 
                         prompt: str, 
                         temperature: float = 0.7, 
                         max_tokens: int = 1000) -> Dict[str, Any]:
        start_time = time.time()
        
        try:
            # Step 1: Generate chain of thought reasoning
            logger.info(f"Starting chain of thought for prompt: {prompt[:100]}...")
            cot_response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": self._generate_cot_prompt(prompt)}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            reasoning = cot_response.choices[0].message.content
            logger.info(f"Generated reasoning: {reasoning[:200]}...")
            
            # Step 2: Generate final answer based on reasoning
            final_response = self.client.chat.completions.create(
                model="chatgpt-4o-latest",
                messages=[
                    {"role": "user", "content": self._generate_summary_prompt(prompt, reasoning)}
                ],
                temperature=temperature,
                max_tokens=max_tokens // 2  # Shorter response for summary
            )
            
            final_answer = final_response.choices[0].message.content
            logger.info(f"Generated final answer: {final_answer[:200]}...")
            
            # Calculate total tokens and time
            total_tokens = (
                cot_response.usage.total_tokens + 
                final_response.usage.total_tokens
            )
            execution_time = time.time() - start_time
            
            # Log metrics
            logger.info(f"Request completed - Tokens: {total_tokens}, Time: {execution_time:.2f}s")
            
            return {
                "id": f"cot-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": "chatgpt-4o-latest-with-cot",
                "usage": {
                    "prompt_tokens": cot_response.usage.prompt_tokens + final_response.usage.prompt_tokens,
                    "completion_tokens": cot_response.usage.completion_tokens + final_response.usage.completion_tokens,
                    "total_tokens": total_tokens
                },
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": final_answer,
                        "reasoning": reasoning  # Include reasoning in response
                    },
                    "finish_reason": "stop",
                    "index": 0
                }]
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise

# Initialize Flask app
app = Flask(__name__)
CORS(app)
# Initialize OpenAI client
client = ChainOfThoughtClient(api_key=os.getenv('OPENAI_API_KEY'))


# Add a health check endpoint
@app.route('/')
def health_check():
    return jsonify({"status": "healthy", "service": "cot-server"})


@app.route('/v1/chat/completions', methods=['POST'])
def chat_completion():
    try:
        data = request.json
        
        # Log incoming request
        logger.info(f"Received request: {data}")
        
        # Extract parameters
        messages = data.get('messages', [])
        temperature = data.get('temperature', 0.7)
        max_tokens = data.get('max_tokens', 1000)
        
        # Get the last user message
        last_message = next(
            (msg['content'] for msg in reversed(messages) 
             if msg['role'] == 'user'),
            None
        )
        
        if not last_message:
            raise ValueError("No user message found in request")
            
        # Generate response with chain of thought
        response = client.generate_response(
            prompt=last_message,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return jsonify({
            "error": {
                "message": str(e),
                "type": "internal_error",
                "code": 500
            }
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)
