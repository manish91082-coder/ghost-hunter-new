"""
P0-ONLINE-TRAINER: Autonomous Continuous Online SGD Trainer Agent
------------------------------------------------------------------
Runs continuous in-memory Online Stochastic Gradient Descent (SGD) auto-tuning
on live Polygon block data, updates AI brain weights in phantomx_ai_brain.pkl,
and persists training knowledge.
"""

import asyncio
import logging
import os
import time
from agent_event_bus import event_bus
from auto_tuner_engine import OnlineSGDAutoTuner

logger = logging.getLogger("P0-ONLINE-TRAINER")

class OnlineTrainerAgent:
    def __init__(self):
        self.agent_id = "P0-ONLINE-TRAINER"
        # Pass model_path so brain persists across swarm restarts
        self.tuner = OnlineSGDAutoTuner(model_path="phantomx_ai_brain.pkl")
        self.train_interval_sec = 120 # Auto-tunes every 2 minutes

    async def start(self):
        logger.info(f"[{self.agent_id}] Autonomous Continuous Online SGD Trainer Active (Tuning Interval: {self.train_interval_sec}s).")
        while True:
            try:
                # Trigger in-memory online SGD weight update on live log records
                tuning_res = self.tuner.tune_on_recent_blocks()
                # Persist updated brain weights to disk
                self.tuner._save_model()
                logger.info(f"[{self.agent_id}] Continuous SGD Auto-Tuning Cycle Complete. Dynamic profit floor & permutation scores updated. Tuned: {tuning_res.get('tuned', False)}")
            except Exception as e:
                logger.debug(f"[{self.agent_id}] Training cycle heartbeat: {e}")
            await asyncio.sleep(self.train_interval_sec)

