"""
P0-RPC-ROUTER: Autonomous RPC Health & Failover Rotation Agent
--------------------------------------------------------------
Monitors node latencies, health-checks endpoints, and publishes RPC_SWITCHED events.
"""

import asyncio
import logging
from agent_event_bus import event_bus
from rpc_manager import rpc_manager

logger = logging.getLogger("P0-RPC-ROUTER")

class RPCRouterAgent:
    def __init__(self):
        self.agent_id = "P0-RPC-ROUTER"
        self.check_interval_sec = 30

    async def start(self):
        logger.info(f"[{self.agent_id}] Autonomous RPC Router Agent Initialized.")
        while True:
            try:
                rpc_manager.refresh_pool()
                best_rpc = rpc_manager.active_instances[0]["url"] if rpc_manager.active_instances else "None"
                latency = rpc_manager.active_instances[0]["latency_ms"] if rpc_manager.active_instances else 999.0
                
                await event_bus.publish(
                    sender=self.agent_id,
                    event_type="RPC_HEALTH_UPDATED",
                    target="ALL",
                    payload={
                        "best_rpc": best_rpc,
                        "latency_ms": latency,
                        "total_healthy_nodes": len(rpc_manager.active_instances)
                    }
                )
            except Exception as e:
                logger.error(f"[{self.agent_id}] Error in RPC health cycle: {e}")
            await asyncio.sleep(self.check_interval_sec)
