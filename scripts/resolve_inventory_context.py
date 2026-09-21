#!/usr/bin/env python3
"""Resolve one canonical Polygon inventory context through the free RPC pool."""
import os
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from phantomx.market_block import acquire_market_block
from phantomx.rpc_failover import build_free_polygon_rpc_pool
ctx=acquire_market_block(build_free_polygon_rpc_pool())
window=int(os.getenv('PHANTOMX_INVENTORY_WINDOW_BLOCKS','5000'))
if window<1: raise SystemExit('window must be positive')
start=max(0,ctx.block_number-window+1)
print(f'PHANTOMX_INVENTORY_PINNED_BLOCK={ctx.block_number}')
print(f'PHANTOMX_INVENTORY_FROM_BLOCK={start}')
print(f'PHANTOMX_INVENTORY_TO_BLOCK={ctx.block_number}')
print(f'SHARED_INVENTORY_BLOCK={ctx.block_number}')