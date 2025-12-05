import asyncio
import json
import logging
import os
from typing import Any

from openai import AsyncOpenAI

from app.core.config import settings
from app.services.voice_engine.llm_driver import NEXUS_SYSTEM_PROMPT
from evals.scorers import SafetyScorer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def generate_response(input_text: str, context: str) -> str:
    """
    Simulates the NEXUS agent response using the system prompt.
    """
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    
    # Format the system prompt with default values for testing
    system_prompt = NEXUS_SYSTEM_PROMPT.format(
        grade=9,
        student_name="Student",
        primary_language="English",
        interests="General",
        learning_style="Visual"
    )

    try:
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "system", "content": f"Context: {context}"},
                {"role": "user", "content": input_text}
            ],
            temperature=0.7,
        )
        content = response.choices[0].message.content
        return content.strip() if content else ""
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return "Error generating response."

async def run_safety_evals():
    """
    Runs safety evaluations on the defined test cases.
    """
    logger.info("Starting Safety Evals...")
    
    # Load test cases
    file_path = os.path.join(os.path.dirname(__file__), "dataset_samples", "safety_test_cases.json")
    with open(file_path, "r") as f:
        test_cases = json.load(f)

    scorer = SafetyScorer()
    results = []

    for case in test_cases:
        logger.info(f"Running case: {case['id']}")
        
        # Generate response
        response = await generate_response(case['input'], case['context'])
        
        # Score response
        score = await scorer.score(case['input'], response)
        reason = await scorer.reason(case['input'], response)
        
        result = {
            "id": case['id'],
            "input": case['input'],
            "response": response,
            "score": score,
            "reason": reason,
            "passed": score == 1.0
        }
        results.append(result)
        
        status = "PASSED" if result['passed'] else "FAILED"
        logger.info(f"Case {case['id']}: {status} - {reason}")

    # Summary
    passed_count = sum(1 for r in results if r['passed'])
    total_count = len(results)
    logger.info(f"Safety Evals Completed. Passed: {passed_count}/{total_count}")

    # Save results
    output_path = os.path.join(os.path.dirname(__file__), "safety_eval_results.json")
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to {output_path}")

if __name__ == "__main__":
    asyncio.run(run_safety_evals())
