from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool
import logging

from src.config import settings
from src.models.inputs import ValidationState
from src.agents.interviewer import interviewer_node, process_answer_node
from src.agents.researcher import conduct_research
from src.agents.free_tier import free_tier_scan
from src.agents.basic_tier import basic_tier_gen
from src.agents.parallel_executor import run_modules_parallel
from src.agents.compiler import compile_standard_report, admin_approval_node

logger = logging.getLogger(__name__)

# Connection pool and checkpointer will be initialized at startup
connection_pool: AsyncConnectionPool = None
checkpointer: AsyncPostgresSaver = None
workflow = StateGraph(ValidationState)

# ============================================
# PHASE 1: INTERVIEW NODES (Free Tier Entry)
# ============================================
workflow.add_node("interviewer", interviewer_node)
workflow.add_node("process_answer", process_answer_node)

# ============================================
# PHASE 2: RESEARCH & FREE REPORT NODES
# ============================================
workflow.add_node("research", conduct_research)
workflow.add_node("free_scan", free_tier_scan)

# ============================================
# PHASE 3: BASIC TIER NODE
# ============================================
workflow.add_node("basic_gen", basic_tier_gen)

# ============================================
# PHASE 4: PARALLEL MODULES (Standard/Premium/Custom)
# ============================================
# Single node that runs all selected modules in parallel
workflow.add_node("parallel_modules", run_modules_parallel)

# ============================================
# PHASE 5: COMPILATION & ADMIN
# ============================================
workflow.add_node("compiler", compile_standard_report)
workflow.add_node("admin_approve", admin_approval_node)

# ============================================
# ENTRY POINT: Start with Interview
# ============================================
workflow.set_entry_point("interviewer")

# ============================================
# ROUTING LOGIC
# ============================================

def route_after_interview(state):
    """
    After interviewer runs:
    - If still asking questions -> END (interrupt for user answer)
    - If interview complete -> proceed to research
    """
    phase = state.get("interview_phase", "asking")
    if phase == "complete":
        return "research"
    else:
        return "wait_for_answer"

workflow.add_conditional_edges("interviewer", route_after_interview, {
    "wait_for_answer": END,  # INTERRUPT: Wait for user to submit answer via API
    "research": "research"
})

# After processing answer, go back to interviewer
workflow.add_edge("process_answer", "interviewer")



# Import module names from constants (single source of truth)
from src.config.constants import STANDARD_MODULE_NAMES


def route_after_research(state):
    """
    After research completes:
    - Free tier -> free_scan (then pause for payment)
    - Basic tier -> basic_gen
    - Standard/Premium/Custom -> parallel_modules (runs all selected modules in parallel)
    """
    inputs = state.get("inputs")
    tier = inputs.tier if inputs else "free"
    
    if tier == "free":
        return "free_scan"
    elif tier == "basic":
        return "basic_gen"
    else:  # standard, premium, or custom - all go to parallel executor
        return "parallel_modules"

# Conditional edges handle the routing
workflow.add_conditional_edges("research", route_after_research, {
    "free_scan": "free_scan",
    "basic_gen": "basic_gen",
    "parallel_modules": "parallel_modules"
})


def route_after_free_scan(state):
    """
    After free scan:
    - Always END to pause for potential upgrade
    - User can call /journey/upgrade to continue with paid tier
    """
    return "pause_for_payment"

workflow.add_conditional_edges("free_scan", route_after_free_scan, {
    "pause_for_payment": END  # INTERRUPT: User sees free report, can upgrade
})


# ============================================
# BASIC TIER EDGES
# ============================================
workflow.add_edge("basic_gen", "admin_approve")


# ============================================
# STANDARD/PREMIUM/CUSTOM EDGES
# ============================================
# Single edge from parallel executor to compiler
workflow.add_edge("parallel_modules", "compiler")
workflow.add_edge("compiler", "admin_approve")


# ============================================
# ADMIN END
# ============================================
workflow.add_edge("admin_approve", END)


# ============================================
# ASYNC LIFECYCLE FUNCTIONS
# ============================================
app_graph = None  # Will be compiled after checkpointer init

from langgraph.checkpoint.memory import MemorySaver
import os

async def init_checkpointer():
    """Initialize the checkpointer at app startup."""
    global connection_pool, checkpointer, app_graph
    
    if os.getenv("USE_MEMORY_SAVER"):
        logger.info("Using MemorySaver (In-Memory Checkpointer)")
        checkpointer = MemorySaver()
        # No connection pool needed
        connection_pool = None
    else:
        # PostgreSQL setup
        connection_pool = AsyncConnectionPool(
            conninfo=settings.DATABASE_URL,
            max_size=20,
            open=False, # Explicitly defer opening to .open() call below
            kwargs={"autocommit": True, "prepare_threshold": 0}
        )
        await connection_pool.open()
        checkpointer = AsyncPostgresSaver(connection_pool)
        await checkpointer.setup()
        logger.info("PostgreSQL Checkpointer Initialized")
    
    # Compile the graph with the initialized checkpointer
    app_graph = workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=["admin_approve"]  # Pause before admin approval for paid tiers
    )

async def close_checkpointer():
    """Close the connection pool at app shutdown."""
    global connection_pool
    if connection_pool:
        await connection_pool.close()
        logger.info("PostgreSQL Connection Pool Closed")