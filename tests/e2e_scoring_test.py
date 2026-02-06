
import asyncio
import httpx
import json
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"

# Test Payload: A "Red Ocean" idea designed to trigger High Competition Score (Bad)
IDEA_DESCRIPTION = """
I want to build a simple Todo List app for students. 
It will have checkboxes and categories. 
There are no unique features, just a basic list.
I have no experience and no money.
"""

async def run_test():
    async with httpx.AsyncClient(timeout=300) as client:
        # 1. SUBMIT IDEA
        logger.info("Step 1: Submitting Idea (Red Ocean Scenario)...")
        response = await client.post(
            f"{BASE_URL}/submit", 
            json={"detailed_description": IDEA_DESCRIPTION, "tier": "free"}
        )
        if response.status_code != 200:
            logger.error(f"Submit Failed: {response.text}")
            return
        
        data = response.json()
        thread_id = data["thread_id"]
        logger.info(f"Thread ID: {thread_id}")
        
        # 2. ANSWER QUESTIONS LOOP
        status = data["status"]
        while status == "question_pending":
            question = data["question"]
            logger.info(f"AI Question: {question}")
            
            # Simple answers confirming it's a generic idea
            answer = "I don't know, just a simple app. No differentiation."
            
            logger.info(f"Answering: {answer}")
            response = await client.post(
                f"{BASE_URL}/answer/{thread_id}",
                json={"answer": answer}
            )
            data = response.json()
            status = data["status"]
            logger.info(f"Status: {status}")
            await asyncio.sleep(1)

        # 3. POLL FOR FREE REPORT
        logger.info("Step 3: Polling for Free Report...")
        while True:
            response = await client.get(f"{BASE_URL}/report/{thread_id}")
            report_data = response.json()
            if report_data["status"] == "free_report_complete" or report_data["status"] == "completed":
                break
            logger.info(f"Report Status: {report_data['status']} - Waiting...")
            await asyncio.sleep(2)
        
        free_report = report_data["report_data"]
        logger.info("FREE REPORT RECEIVED")
        
        # VERIFY FREE REPORT SCORING
        scores = free_report["scores"]
        comp_score = scores["competition_intensity"]["score"]
        comp_reason = scores["competition_intensity"]["reasoning"]
        
        logger.info(f"Free Tier Competition Score: {comp_score}/10 (Should be High/Bad)")
        logger.info(f"Reasoning: {comp_reason}")
        
        if comp_score < 7:
            logger.error("FAILURE: Competition Score is too low for a generic Todo App! Expected 8-10 (Bad).")
        else:
            logger.info("SUCCESS: Competition Score is High (Correctly Inverted Logic).")

        if not comp_reason:
             logger.error("FAILURE: No reasoning provided!")
        else:
             logger.info(f"SUCCESS: Reasoning present: '{comp_reason}'")

        # 4. UPGRADE TO BASIC
        logger.info("Step 4: Upgrading to BASIC...")
        response = await client.post(
            f"{BASE_URL}/upgrade/{thread_id}",
            json={"tier": "basic"}
        )
        logger.info(f"Upgrade Response: {response.json()}")

        # POLL FOR BASIC REPORT
        while True:
            response = await client.get(f"{BASE_URL}/report/{thread_id}")
            report_data = response.json()
            # Basic report is ready when report_data contains 'executive_summary' and tier is basic
            data_content = report_data.get("report_data", {})
            if data_content and data_content.get("tier") == "basic":
                break
            logger.info(f"Basic Report Status: {report_data['status']} - Waiting...")
            await asyncio.sleep(5)

        logger.info("BASIC REPORT RECEIVED")
        basic_report = report_data["report_data"]
        
        # VERIFY BASIC REPORT SCORING
        basic_scores = basic_report["scores"]
        basic_comp_score = basic_scores["competition_analysis"]["score"]
        basic_reason = basic_scores["competition_analysis"]["reasoning"]
        
        logger.info(f"Basic Tier Competition Score: {basic_comp_score}/10")
        logger.info(f"Reasoning: {basic_reason}")
        
        if basic_comp_score < 7:
             logger.error("FAILURE: Basic Competition Score too low!")

        # 5. UPGRADE TO STANDARD
        logger.info("Step 5: Upgrading to STANDARD...")
        response = await client.post(
            f"{BASE_URL}/upgrade/{thread_id}",
            json={"tier": "standard"}
        )
        
        # POLL FOR STANDARD REPORT
        while True:
            response = await client.get(f"{BASE_URL}/report/{thread_id}")
            report_data = response.json()
            data_content = report_data.get("report_data", {})
            
            # Standard report ready when modules are present
            if data_content and data_content.get("tier") == "standard" and "modules" in data_content:
                break
            
            # Check for error
            if report_data["status"] == "failed":
                logger.error(f"Generate Failed: {report_data.get('error')}")
                return

            logger.info(f"Standard Report Status: {report_data['status']} - Waiting...")
            await asyncio.sleep(5)
            
        logger.info("STANDARD REPORT RECEIVED")
        std_report = report_data["report_data"]
        
        # VERIFY STANDARD SCORE BREAKDOWN
        std_scores = std_report["score_breakdown"]
        # Standard report structure might be slightly different in Python dict vs JSON output from model
        # Let's check the structure printed to log if needed
        
        std_comp_score = std_scores["competition_analysis"]["score"]
        std_reason = std_scores["competition_analysis"]["reasoning"]
        
        logger.info(f"Standard Assessment Competition Score: {std_comp_score}/10")
        logger.info(f"Reasoning: {std_reason}")
        
        if std_comp_score < 7:
             logger.error("FAILURE: Standard Competition Score too low!")

if __name__ == "__main__":
    asyncio.run(run_test())
