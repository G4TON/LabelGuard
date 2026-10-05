import os
import json
from google import genai
from app.config import config

class AIService:
    def __init__(self):
        self.is_demo = config.DEMO_MODE
        self.api_key = config.GEMINI_API_KEY
        self.client = None
        if not self.is_demo and self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        
    def suggest_qualification_pack(self, worker_data, available_qps):
        if self.is_demo or not self.client:
            return self._demo_suggest_qp(worker_data, available_qps)
            
        # Real AI implementation
        prompt = f"""
        Given the worker details: {json.dumps(worker_data)}
        And available qualification packs: {json.dumps(available_qps)}
        
        Suggest the best matching qualification pack.
        Return ONLY valid JSON with this structure:
        {{
            "suggested_qp_id": "QP_ID",
            "confidence": 0.0 to 1.0,
            "matching_reasons": "reasoning text",
            "potential_mismatches": "mismatch text",
            "recommendation": "recommendation for assessor"
        }}
        """
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    response_mime_type="application/json",
                )
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"AI Error: {e}")
            return self._demo_suggest_qp(worker_data, available_qps)
            
    def _demo_suggest_qp(self, worker_data, available_qps):
        return {
            "suggested_qp_id": "QP-DEMO-001",
            "confidence": 0.85,
            "matching_reasons": "Worker mentioned plumbing experience matching the general plumber QP.",
            "potential_mismatches": "Worker did not explicitly mention welding high-pressure joints.",
            "recommendation": "Assessor should verify high-pressure welding skills in person."
        }

    def review_evidence(self, task_description, rubric, evidence_text):
        if self.is_demo or not self.client:
            return self._demo_review_evidence(task_description)
            
        prompt = f"""
        Task: {task_description}
        Rubric: {json.dumps(rubric)}
        Evidence: {evidence_text}
        
        Review the evidence against the rubric.
        Return ONLY valid JSON with this structure:
        {{
            "suggested_score": 1, 2, 3, or 4,
            "observation": "detailed observation",
            "confidence": 0.0 to 1.0,
            "requires_human": true or false
        }}
        """
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    response_mime_type="application/json",
                )
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"AI Error: {e}")
            return self._demo_review_evidence(task_description)
            
    def _demo_review_evidence(self, task_description):
        return {
            "suggested_score": 3,
            "observation": "Demo Observation: The evidence appears to show basic competency for the task.",
            "confidence": 0.9,
            "requires_human": True
        }

ai_service = AIService()
