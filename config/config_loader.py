"""
PhantomX Dynamic Configuration Loader (config/config_loader.py)
================================================================
Zero Hardcoding Policy Enforcer.
Loads settings dynamically from config/settings.json and environment variables.
"""

import os
import json
import sys

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

CONFIG_DIR = os.path.abspath(os.path.dirname(__file__))
SETTINGS_FILE = os.path.join(CONFIG_DIR, "settings.json")

_cached_config = None

def load_config(force_reload=False) -> dict:
    global _cached_config
    if _cached_config is not None and not force_reload:
        return _cached_config

    if not os.path.exists(SETTINGS_FILE):
        raise FileNotFoundError(f"CRITICAL CONFIG ERROR: '{SETTINGS_FILE}' does not exist!")

    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)

    # Environment variable overrides
    env_mode = os.getenv("PHANTOMX_EXECUTION_MODE") or os.getenv("EXECUTION_MODE")
    if env_mode:
        config["execution_mode"] = env_mode.upper()
        if env_mode.upper() in ("LIVE", "LIVE_MAINNET"):
            config["dry_run"] = False
        elif env_mode.upper() == "SHADOW":
            config["dry_run"] = True

    env_dry_run = os.getenv("PHANTOMX_DRY_RUN") if os.getenv("PHANTOMX_DRY_RUN") is not None else os.getenv("DRY_RUN")
    if env_dry_run is not None:
        config["dry_run"] = env_dry_run.lower() in ("true", "1", "yes")
        if not config["dry_run"]:
            config["execution_mode"] = "LIVE_MAINNET"

    _cached_config = config
    return config

def get_setting(key_path: str, default=None):
    """
    Retrieve nested setting using dot notation.
    Example: get_setting("blockchain.network")
    """
    config = load_config()
    keys = key_path.split(".")
    curr = config
    for k in keys:
        if isinstance(curr, dict) and k in curr:
            curr = curr[k]
        else:
            return default
    return curr

def is_dry_run() -> bool:
    return get_setting("dry_run", True)

def get_execution_mode() -> str:
    return get_setting("execution_mode", "SHADOW")

if __name__ == "__main__":
    cfg = load_config()
    print("================================================================================")
    print("✅ PhantomX Dynamic Configuration Loaded (Zero Hardcoding Enforced)")
    print("================================================================================")
    print(f"Mode: {cfg['execution_mode']} | Dry Run: {cfg['dry_run']}")
    print(f"Network: {cfg['blockchain']['network']} (Chain ID: {cfg['blockchain']['chain_id']})")
    print(f"Contract: {cfg['contracts']['universal_executor']}")
    print(f"Target Pairs: {cfg['trading_parameters']['target_pairs']}")
