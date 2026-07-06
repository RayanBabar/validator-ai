import asyncio
import os
import dotenv
dotenv.load_dotenv()

from src.graph.workflow import init_checkpointer, close_checkpointer, app_graph
from src.utils.supabase import get_supabase_client

async def test():
    await init_checkpointer()
    
    # Let's check a thread ID that is completed
    thread_id = "5af709ab-f2fa-4802-b7b9-8449dc858b4a"
    config = {"configurable": {"thread_id": thread_id}}
    
    print("Fetching current state...")
    snapshot = await app_graph.aget_state(config)
    print("Snapshot values keys:", snapshot.values.keys() if snapshot.values else None)
    print("interview_phase:", snapshot.values.get("interview_phase"))
    print("workflow_phase:", snapshot.values.get("workflow_phase"))
    print("final_report:", snapshot.values.get("final_report") is not None)
    
    print("\nRunning remaining graph nodes...")
    try:
        async for step in app_graph.astream(None, config):
            print("Step executed:", step)
    except Exception as e:
        print("Error during graph execution:", e)
        
    print("\nChecking state after run...")
    snapshot = await app_graph.aget_state(config)
    print("interview_phase:", snapshot.values.get("interview_phase"))
    print("workflow_phase:", snapshot.values.get("workflow_phase"))
    print("final_report:", snapshot.values.get("final_report") is not None)
    
    await close_checkpointer()

if __name__ == "__main__":
    asyncio.run(test())
