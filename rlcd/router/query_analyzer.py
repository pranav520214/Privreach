import json
from typing import Dict, Any
from llama_cpp import Llama
from core.schemas.rlcd_schemas import ExecutionPlan

class RLCDRouter:
    def __init__(self, llm: Llama):
        self.llm = llm
        
    def analyze_query(self, query: str) -> ExecutionPlan:
        """
        Analyzes the query and returns a strongly-typed ExecutionPlan.
        """
        schema = ExecutionPlan.model_json_schema()
        
        system_prompt = (
            "You are the RLCD (Router, Logic, Control, Decision) Router for Prva Veda, "
            "a critical scientific research system. Your job is to analyze the user's query "
            "and output a JSON object that strictly conforms to the provided JSON schema. "
            "Determine the domain, task type, risk level, and required tools."
        )
        
        # We use chat completion with response_format to enforce JSON schema output
        response = self.llm.create_chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze this query:\n\n{query}"}
            ],
            response_format={
                "type": "json_object",
                "schema": schema
            },
            temperature=0.0,
            max_tokens=512
        )
        
        # Extract the JSON string from the response
        json_str = response["choices"][0]["message"]["content"]
        
        # Parse into the Pydantic model
        try:
            plan_dict = json.loads(json_str)
            plan = ExecutionPlan(**plan_dict)
            return plan
        except Exception as e:
            print(f"Failed to parse RLCD Router output: {json_str}")
            raise e
