import asyncio
import json
import os

# Disable webhooks and other side effects for inspection
os.environ["USE_MEMORY_SAVER"] = "False" 

from src.graph.workflow import app_graph, init_checkpointer

async def check_state(thread_id: str):
    # Initialize checkpointer so app_graph is compiled
    await init_checkpointer()
    from src.graph.workflow import app_graph
    
    config = {"configurable": {"thread_id": thread_id}}
    state = await app_graph.aget_state(config)
    
    if not state or not state.values:
        print(f"No state found for thread_id: {thread_id}")
        return

    # Clean up state for printing
    values = state.values.copy()
    # Remove large context objects if present to keep output readable
    if "search_context" in values:
        values["search_context"] = f"<{len(values['search_context'])} chars>"
    
    print(json.dumps(values, indent=2, default=str))

if __name__ == "__main__":
    import sys
    thread_id = sys.argv[1] if len(sys.argv) > 1 else "18f8b19d-4aeb-433e-91fd-a4bd08055a91"
    asyncio.run(check_state(thread_id))
