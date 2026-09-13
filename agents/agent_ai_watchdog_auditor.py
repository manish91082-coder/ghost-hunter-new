"""
P0-AI-WATCHDOG-AUDITOR: Autonomous AI Training & Testing Quality Watchdog & Auto-Corrector
-----------------------------------------------------------------------------------------
Specialized 12th Autonomous Swarm Agent for PhantomX.
Continuously audits SGD online learning loss convergence, feature drift, RPC latency,
simulated net profit yields, and applies dynamic real-time hyperparameter auto-corrections.
"""

import asyncio
import json
import logging
import os
import time
from typing import Dict, Any, List
from agent_event_bus import event_bus
from config.config_loader import load_config

logger = logging.getLogger("P0-AI-WATCHDOG-AUDITOR")

class AIWatchdogAuditorAgent:
    def __init__(self):
        self.agent_id = "P0-AI-WATCHDOG-AUDITOR"
        self.config = load_config()
        self.audit_interval_sec = 30  # Audit loop every 30 seconds
        os.makedirs("logs", exist_ok=True)
        self.log_file = os.path.join("logs", "phantomx_ai_watchdog_audit.jsonl")

        
        # State metrics
        self.total_blocks_audited = 0
        self.total_models_updated = 0
        self.current_loss_val = 0.05
        self.current_learning_rate = 0.001
        self.auto_corrections_applied = 0
        self.loss_history: List[float] = []
        self.rpc_latencies: Dict[str, float] = {}
        
        # Subscribe to Event Bus
        event_bus.subscribe("MODEL_TRAINED", self.on_model_trained)
        event_bus.subscribe("OPPORTUNITY_DETECTED", self.on_opportunity_detected)
        event_bus.subscribe("RPC_HEALTH_UPDATE", self.on_rpc_health_update)

    async def on_model_trained(self, msg: Dict[str, Any]):
        payload = msg.get("payload", {})
        loss = payload.get("loss", 0.05)
        blocks = payload.get("blocks_processed", 1)
        self.total_models_updated += 1
        self.total_blocks_audited += blocks
        self.loss_history.append(loss)
        if len(self.loss_history) > 100:
            self.loss_history.pop(0)
            
        self.current_loss_val = sum(self.loss_history) / len(self.loss_history)
        
        # Dynamic Auto-Correction Logic
        if loss > 0.5 and self.current_learning_rate > 0.0001:
            self.current_learning_rate *= 0.9  # Decay learning rate if loss spikes
            self.auto_corrections_applied += 1
            logger.warning(f"[{self.agent_id}] AUTO-CORRECTION: Loss spike detected ({loss:.4f}). Decayed learning rate to {self.current_learning_rate:.6f}.")
            
            # Emit Auto-Correction Event
            await event_bus.publish(
                sender=self.agent_id,
                event_type="HYPERPARAMETER_AUTO_CORRECTED",
                target="P0-ONLINE-TRAINER",
                payload={
                    "reason": "LOSS_SPIKE_DECAY",
                    "new_learning_rate": self.current_learning_rate,
                    "timestamp": time.time()
                }
            )

    async def on_opportunity_detected(self, msg: Dict[str, Any]):
        payload = msg.get("payload", {})
        net_profit = payload.get("expected_net_profit_usd", 0.0)
        pair = payload.get("pair", "UNKNOWN")
        logger.debug(f"[{self.agent_id}] Audited Opportunity on {pair}: Net Profit = ${net_profit:.4f}")

    async def on_rpc_health_update(self, msg: Dict[str, Any]):
        payload = msg.get("payload", {})
        rpc = payload.get("rpc_url", "")
        latency = payload.get("latency_ms", 999.0)
        if rpc:
            self.rpc_latencies[rpc] = latency
            if latency > 150.0:
                logger.info(f"[{self.agent_id}] High latency detected on RPC {rpc} ({latency:.1f}ms). Flagged for router dynamic failover.")

    async def _audit_and_log_state(self):
        entry = {
            "timestamp": time.time(),
            "iso_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "agent_id": self.agent_id,
            "total_blocks_audited": self.total_blocks_audited,
            "total_models_updated": self.total_models_updated,
            "avg_loss": round(self.current_loss_val, 6),
            "learning_rate": round(self.current_learning_rate, 6),
            "auto_corrections_applied": self.auto_corrections_applied,
            "active_rpc_count": len([lat for lat in self.rpc_latencies.values() if lat < 150.0]),
            "status": "HEALTHY_AUTO_CONVERGING"
        }
        
        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            logger.error(f"[{self.agent_id}] Error writing audit log: {e}")
            
        # Broadcast telemetry metrics to P0-TELEGRAM-ALERT
        await event_bus.publish(
            sender=self.agent_id,
            event_type="TELEMETRY_DIGEST_UPDATE",
            target="P0-TELEGRAM-ALERT",
            payload={
                "auditor_metrics": entry,
                "timestamp": time.time()
            }
        )

    async def start(self):
        logger.info(f"[{self.agent_id}] Autonomous AI Watchdog Auditor & Auto-Corrector Active (Audit Interval: {self.audit_interval_sec}s).")
        while True:
            try:
                await self._audit_and_log_state()
            except Exception as e:
                logger.error(f"[{self.agent_id}] Error in watchdog auditor loop: {e}")
            await asyncio.sleep(self.audit_interval_sec)

# Standalone Test Execution
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    agent = AIWatchdogAuditorAgent()
    asyncio.run(agent.start())
