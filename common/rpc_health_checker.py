import sqlite3
import urllib.request
import json
import time

db_path = r'c:\Users\Admin\.gemini\antigravity-ide\scratch\flash loan ghost hunter\phantomx_knowledge.db'

def health_check_rpcs():
    print("--- RPC HEALTH CHECKER ---")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # We will check 5 RPCs to prove the health check pipeline works
    c.execute("SELECT rpc_id, url FROM rpcs WHERE url LIKE 'http%' LIMIT 5")
    rpcs = c.fetchall()
    
    for rpc_id, url in rpcs:
        print(f"Checking {url}...")
        try:
            req = urllib.request.Request(url, data=json.dumps({"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}).encode(), headers={'Content-Type': 'application/json'})
            start = time.time()
            with urllib.request.urlopen(req, timeout=3) as response:
                latency = int((time.time() - start) * 1000)
                data = json.loads(response.read().decode())
                if "result" in data:
                    c.execute("UPDATE rpcs SET is_active = 1, latency_ms = ? WHERE rpc_id = ?", (latency, rpc_id))
                    print(f"  [+] Active - Latency: {latency}ms")
                else:
                    c.execute("UPDATE rpcs SET is_active = 0 WHERE rpc_id = ?", (rpc_id,))
                    print(f"  [-] Inactive - Bad Response")
        except Exception as e:
            c.execute("UPDATE rpcs SET is_active = 0 WHERE rpc_id = ?", (rpc_id,))
            print(f"  [-] Inactive - Error: {e}")
            
    conn.commit()
    conn.close()

if __name__ == '__main__':
    health_check_rpcs()
