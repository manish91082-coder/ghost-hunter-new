"""
PhantomX Autonomous Multi-Agent Swarm Orchestrator (phantomx_multiagent_swarm.py)
----------------------------------------------------------------------------------
Orchestrates the 12 specialized autonomous AI agents in parallel:
1. P0-RPC-ROUTER: 25-RPC Pool Health & Failover Rotation Agent
2. P0-QUANT: Microstructure Quant & Dynamic L* Sizing Agent
3. P0-SIMULATOR: Avionics 5ms Pre-Flight eth_call Simulator Agent
4. P0-SIGNER-BROADCASTER: Dynamic EIP-1559 Signer & Mempool Broadcaster Agent
5. P0-RECEIPT: On-Chain Block Receipt Auditor Agent
6. P0-DIAG: Atomic Reason Diagnostic Logger Agent
7. P0-GOV: Zero-Loss Governor (> $0.20 USD Min Net Profit Guard) Agent
8. P0-TELEGRAM-ALERT: Telemetry 15-Min Deep Insight Digest & Trade Alert Agent
9. P0-COLAB-SYNC: State Persistence & Manifest Backup Agent
10. P0-ONLINE-TRAINER: Continuous Online SGD Auto-Tuning Agent
11. P0-AI-WATCHDOG-AUDITOR: AI Training & Testing Auto-Corrector Agent
12. P0-WATCHER-MONITOR: Process Keep-Alive & System Resilience Agent

Conforms strictly to 10 Immutable Protocols (0% Hardcoding, >$0.20 USD Profit, Sub-15ms Speed).
"""

import asyncio
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent_event_bus import event_bus
from agents.agent_rpc_router import RPCRouterAgent
from agents.agent_quant import QuantV2Agent, QuantV3Agent
from agents.agent_simulator import SimulatorAgent
from agents.agent_signer_broadcaster import SignerBroadcasterAgent
from agents.agent_diagnostic_receipt import ReceiptDiagnosticAgent
from agents.agent_governor import GovernorAgent
from agents.agent_telegram_notifier import TelegramNotifierAgent
from agents.agent_colab_sync import ColabSyncAgent
from agents.agent_online_trainer import OnlineTrainerAgent
from agents.agent_ai_watchdog_auditor import AIWatchdogAuditorAgent
from agents.agent_watcher_monitor import WatcherMonitorAgent
from config.config_loader import load_config
from utils.process_guard import ProcessGuard

# Ensure logs directory exists and set up log routing
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join("logs", "phantomx_swarm.log"), encoding="utf-8")
    ]
)
logger = logging.getLogger("PHANTOMX-SWARM")

class MultiAgentSwarmOrchestrator:
    def __init__(self):
        self.config = load_config()
        self.guard = ProcessGuard(lock_file="phantomx_engine.pid", script_name="phantomx_multiagent_swarm.py")
        self.rpc_router_agent = RPCRouterAgent()
        self.quant_v2_agent = QuantV2Agent()
        self.quant_v3_agent = QuantV3Agent()
        self.simulator_agent = SimulatorAgent()
        self.signer_broadcaster_agent = SignerBroadcasterAgent()
        self.receipt_diag_agent = ReceiptDiagnosticAgent()
        self.governor_agent = GovernorAgent()
        self.telegram_agent = TelegramNotifierAgent()
        self.colab_sync_agent = ColabSyncAgent()
        self.online_trainer_agent = OnlineTrainerAgent()
        self.ai_watchdog_agent = AIWatchdogAuditorAgent()
        self.watcher_monitor_agent = WatcherMonitorAgent()

    @property
    def quant_agent(self):
        return self.quant_v2_agent

    async def run_swarm(self, duration_sec: int = 0):
        # Acquire single-instance process lock & clean duplicate processes
        self.guard.acquire_lock()

        logger.info("================================================================================")
        logger.info("🚀 PHANTOMX AUTONOMOUS MULTI-AGENT SWARM INITIALIZING (12 SPECIALIZED AGENTS)...")
        logger.info("================================================================================")
        
        # Start event bus
        bus_task = asyncio.create_task(event_bus.start())
        
        # Start all specialized agents in parallel tasks (decoupled V2 and V3 quants)
        tasks = [
            asyncio.create_task(self.rpc_router_agent.start()),
            asyncio.create_task(self.quant_v2_agent.start()),
            asyncio.create_task(self.quant_v3_agent.start()),
            asyncio.create_task(self.simulator_agent.start()),
            asyncio.create_task(self.signer_broadcaster_agent.start()),
            asyncio.create_task(self.receipt_diag_agent.start()),
            asyncio.create_task(self.governor_agent.start()),
            asyncio.create_task(self.telegram_agent.start()),
            asyncio.create_task(self.colab_sync_agent.start()),
            asyncio.create_task(self.online_trainer_agent.start()),
            asyncio.create_task(self.ai_watchdog_agent.start()),
            asyncio.create_task(self.watcher_monitor_agent.start())
        ]
        
        logger.info("🟢 ALL 12 AUTONOMOUS AGENTS (DECOUPLED V2/V3 QUANTS) STARTED & LISTENING ON SUB-10MS EVENT BUS.")

        
        try:
            if duration_sec > 0:
                await asyncio.sleep(duration_sec)
                logger.info(f"Stopping swarm after {duration_sec}s test run...")
                for t in tasks:
                    t.cancel()
                event_bus.stop()
                bus_task.cancel()
            else:
                await asyncio.gather(*tasks, bus_task)
        finally:
            self.guard.release_lock()

if __name__ == "__main__":
    swarm = MultiAgentSwarmOrchestrator()
    try:
        asyncio.run(swarm.run_swarm())
    except KeyboardInterrupt:
        logger.info("Swarm stopped by user.")
    finally:
        swarm.guard.release_lock()

