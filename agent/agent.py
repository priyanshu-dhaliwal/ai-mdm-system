#!/usr/bin/env python3
"""
MDM Agent — runs on Android devices via Termux or ADB shell.
Connects to MDM server, sends heartbeats, executes commands.
"""
import asyncio, websockets, json, subprocess, os, time, argparse

CONFIG_PATH = "/data/local/tmp/mdm_config.json"
LOG_PATH    = "/data/local/tmp/mdm_agent.log"

def load_config():
    defaults = {"server_url":"ws://192.168.1.100:8000/ws/device",
                "device_id":"device-001","token":"demo_token",
                "device_name":"Android-Device"}
    try:
        with open(CONFIG_PATH) as f: return {**defaults, **json.load(f)}
    except: return defaults

def get_battery():
    try:
        out = subprocess.check_output(["dumpsys","battery"],text=True)
        for line in out.splitlines():
            if "level" in line: return int(line.split(":")[1].strip())
    except: return -1

def is_rooted():
    return any(os.path.exists(p) for p in ["/system/bin/su","/system/xbin/su","/su/bin/su"])

def get_ip():
    try: return subprocess.check_output(["ip","route"],text=True).split()[-1]
    except: return "unknown"

def get_cpu():
    try:
        with open("/proc/loadavg") as f: return float(f.read().split()[0])*10
    except: return 0.0

async def handle_command(data: dict):
    cmd = data.get("command","")
    print(f"[MDM] Command received: {cmd}")
    try:
        if   cmd == "lock_screen":   subprocess.run(["input","keyevent","26"])
        elif cmd == "reboot":        subprocess.run(["reboot"])
        elif cmd == "get_battery":   print(f"Battery: {get_battery()}%")
        elif cmd == "enable_airplane":
            subprocess.run(["settings","put","global","airplane_mode_on","1"])
        elif cmd == "disable_wifi":
            subprocess.run(["svc","wifi","disable"])
        elif cmd == "enable_wifi":
            subprocess.run(["svc","wifi","enable"])
        elif cmd == "push_message":
            msg = data.get("params",{}).get("message","MDM Alert")
            print(f"[MDM] Notification: {msg}")
        elif cmd.startswith("uninstall_app:"):
            pkg = cmd.split(":")[1]
            subprocess.run(["pm","uninstall",pkg])
        elif cmd == "take_screenshot":
            subprocess.run(["screencap","-p","/sdcard/mdm_screenshot.png"])
    except Exception as e:
        print(f"[MDM] Command error: {e}")

async def run():
    config = load_config()
    uri    = f"{config['server_url']}/{config['device_id']}"
    print(f"[MDM] Connecting to {uri}")

    while True:
        try:
            async with websockets.connect(uri) as ws:
                print("[MDM] Connected ✅")

                async def heartbeat():
                    while True:
                        await ws.send(json.dumps({
                            "type":      "heartbeat",
                            "battery":   get_battery(),
                            "is_rooted": is_rooted(),
                            "ip":        get_ip(),
                            "cpu":       get_cpu(),
                            "ram":       0, "net_rx": 0, "net_tx": 0,
                        }))
                        await asyncio.sleep(30)

                async def listen():
                    async for msg in ws:
                        await handle_command(json.loads(msg))

                await asyncio.gather(heartbeat(), listen())

        except Exception as e:
            print(f"[MDM] Disconnected: {e}. Reconnecting in 10s...")
            await asyncio.sleep(10)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=CONFIG_PATH)
    args = parser.parse_args()
    if args.config != CONFIG_PATH:
        CONFIG_PATH = args.config
    asyncio.run(run())
