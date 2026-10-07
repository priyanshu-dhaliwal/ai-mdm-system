#!/usr/bin/env python3
"""Bulk MDM Agent Installer — deploys agent to all connected Android devices in parallel."""
import subprocess, sys, os, json, time, threading, uuid, argparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

console = Console()
ADB = "adb"
REMOTE_AGENT = "/data/local/tmp/mdm_agent.py"
REMOTE_CFG   = "/data/local/tmp/mdm_config.json"
AGENT_SCRIPT = os.path.join(os.path.dirname(__file__), "agent.py")

def run_adb(serial, *args, timeout=30):
    try:
        r = subprocess.run([ADB,"-s",serial]+list(args), capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired: return -1,"",f"Timeout after {timeout}s"
    except FileNotFoundError:         return -1,"","adb not found. Run: sudo apt install adb"

def get_connected_devices():
    r = subprocess.run([ADB,"devices","-l"], capture_output=True, text=True)
    devices = []
    for line in r.stdout.splitlines()[1:]:
        if not line.strip() or "offline" in line: continue
        parts = line.split()
        if len(parts) < 2 or parts[1] not in ("device","unauthorized"): continue
        serial = parts[0]
        _, model,   _ = run_adb(serial,"shell","getprop","ro.product.model")
        _, android, _ = run_adb(serial,"shell","getprop","ro.build.version.release")
        _, mfr,     _ = run_adb(serial,"shell","getprop","ro.product.manufacturer")
        _, bat_raw, _ = run_adb(serial,"shell","dumpsys","battery")
        battery = 0
        for bl in bat_raw.splitlines():
            if "level" in bl:
                try: battery = int(bl.split(":")[1].strip())
                except: pass
        devices.append({"serial":serial,"status":parts[1],"model":model or "Unknown",
                         "manufacturer":mfr or "Unknown","android":android or "?",
                         "battery":battery,"device_id":str(uuid.uuid4())})
    return devices

def install_device(device, server_ip, server_port, token, progress_cb=None):
    serial    = device["serial"]
    device_id = device["device_id"]
    steps     = []

    def step(name, fn):
        ok, msg = fn()
        steps.append({"step":name,"ok":ok,"msg":msg})
        if progress_cb: progress_cb(serial, name)
        return ok, msg

    def check_auth():
        rc,_,e = run_adb(serial,"shell","echo","ok")
        return (True,"Authorized") if rc==0 else (False,f"Not authorized: {e}")

    def check_python():
        rc,out,_ = run_adb(serial,"shell","which","python3")
        if rc==0 and out: return True,f"Python3 at {out}"
        rc2,_,e = run_adb(serial,"shell","pkg install -y python",timeout=120)
        return (True,"Installed via Termux") if rc2==0 else (False,"Python3 not found. Install Termux")

    def install_pkgs():
        for pkg in ["websockets"]:
            rc,_,e = run_adb(serial,"shell",f"python3 -m pip install {pkg} -q",timeout=120)
            if rc!=0: return False,f"pip {pkg} failed: {e}"
        return True,"Packages installed"

    def push_agent():
        if not os.path.exists(AGENT_SCRIPT): return False,f"Missing: {AGENT_SCRIPT}"
        rc,_,e = run_adb(serial,"push",AGENT_SCRIPT,REMOTE_AGENT)
        return (True,"Agent pushed") if rc==0 else (False,f"Push failed: {e}")

    def configure():
        cfg = json.dumps({"server_url":f"ws://{server_ip}:{server_port}/ws/device",
                           "device_id":device_id,"token":token,
                           "device_name":f"{device['manufacturer']}-{device['model']}"})
        rc,_,e = run_adb(serial,"shell",f"echo '{cfg}' > {REMOTE_CFG}")
        return (True,"Configured") if rc==0 else (False,f"Config failed: {e}")

    def start():
        run_adb(serial,"shell",
                f"nohup python3 {REMOTE_AGENT} --config {REMOTE_CFG} "
                f"> /data/local/tmp/mdm_agent.log 2>&1 &")
        time.sleep(2)
        _,pids,_ = run_adb(serial,"shell","pgrep -f mdm_agent.py")
        return (True,f"Running PID {pids.strip()}") if pids.strip() else (False,"Process not found")

    def verify():
        time.sleep(2)
        _,log,_ = run_adb(serial,"shell","cat /data/local/tmp/mdm_agent.log")
        return True, ("Connecting..." if "Connecting" in log or "Connected" in log else "Deployed (check manually)")

    ok = True
    for name, fn in [("Check Auth",check_auth),("Check Python",check_python),
                     ("Install Packages",install_pkgs),("Push Agent",push_agent),
                     ("Configure",configure),("Start Agent",start),("Verify",verify)]:
        ok, msg = step(name, fn)
        if not ok: break

    return {"serial":serial,"device_id":device_id,"model":device["model"],
            "success":ok,"steps":steps,"message":msg}

def main():
    parser = argparse.ArgumentParser(description="Bulk MDM Agent Installer",
        epilog="Examples:\n  python3 bulk_installer.py --server 192.168.1.100\n"
               "  python3 bulk_installer.py --server 192.168.1.100 --wifi-scan 192.168.1.0/24\n"
               "  python3 bulk_installer.py --uninstall\n  python3 bulk_installer.py --list",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--server",    default="192.168.1.100")
    parser.add_argument("--port",      type=int, default=8000)
    parser.add_argument("--token",     default="demo_token")
    parser.add_argument("--serials",   default="")
    parser.add_argument("--wifi-scan", default="")
    parser.add_argument("--workers",   type=int, default=5)
    parser.add_argument("--uninstall", action="store_true")
    parser.add_argument("--list",      action="store_true")
    parser.add_argument("--output",    default="enrolled_devices.json")
    args = parser.parse_args()

    console.print("[bold red]\n ╔╦╗╔╦╗╔╦╗  Bulk MDM Installer\n  ║║║║║╔╩╗  Kali Linux | ADB\n ═╩╝╩ ╩╚═╝  v1.0[/bold red]")

    # WiFi connect
    if args.wifi_scan:
        r = subprocess.run(["nmap","-p","5555","--open","-oG","-",args.wifi_scan],
                           capture_output=True,text=True,timeout=60)
        for line in r.stdout.splitlines():
            if "5555/open" in line:
                ip = line.split()[1]
                subprocess.run([ADB,"connect",f"{ip}:5555"],capture_output=True,timeout=10)

    all_devices = get_connected_devices()
    if not all_devices:
        console.print(Panel("[red]No devices found!\n\nCheck USB debugging is enabled and cable is connected.\nRun: adb devices[/red]",
                            title="No Devices",border_style="red")); sys.exit(1)

    # Print device table
    t = Table(title="Connected Devices"); 
    t.add_column("Serial"); t.add_column("Model"); t.add_column("Android"); t.add_column("Battery"); t.add_column("Status")
    for d in all_devices: t.add_row(d["serial"],f"{d['manufacturer']} {d['model']}",d["android"],f"{d['battery']}%",d["status"])
    console.print(t)

    if args.list: sys.exit(0)

    target = [d for d in all_devices if d["status"]=="device"]
    if args.serials:
        sf = set(args.serials.split(","))
        target = [d for d in target if d["serial"] in sf]

    if not target: console.print("[red]No authorized devices.[/red]"); sys.exit(1)

    if args.uninstall:
        console.print(f"[yellow]Uninstalling from {len(target)} devices...[/yellow]")
        for d in target:
            run_adb(d["serial"],"shell","pkill -f mdm_agent.py")
            for f in [REMOTE_AGENT, REMOTE_CFG, "/data/local/tmp/mdm_agent.log"]:
                run_adb(d["serial"],"shell",f"rm -f {f}")
            console.print(f"  [green]✓ {d['serial']}[/green]")
        return

    confirm = input(f"\nInstall on {len(target)} device(s)? [y/N]: ")
    if confirm.lower() != "y": sys.exit(0)

    results = []; lock = threading.Lock()

    with Progress(SpinnerColumn(), TextColumn("{task.description}"),
                  BarColumn(), TaskProgressColumn(), console=console) as prog:
        overall = prog.add_task("Installing...", total=len(target))
        tasks   = {d["serial"]: prog.add_task(f"{d['model'][:20]} ({d['serial'][:10]})", total=7) for d in target}

        def do_install(device):
            def cb(serial, msg): prog.advance(tasks[serial])
            result = install_device(device, args.server, args.port, args.token, progress_callback=cb)
            with lock: results.append(result); prog.advance(overall)
            return result

        with ThreadPoolExecutor(max_workers=args.workers) as exe:
            for f in as_completed([exe.submit(do_install,d) for d in target]): f.result()

    # Results
    rt = Table(title="Results")
    rt.add_column("Serial"); rt.add_column("Model"); rt.add_column("Status"); rt.add_column("Message")
    for r in results:
        rt.add_row(r["serial"],r.get("model","?"),
                   "✅ Success" if r["success"] else "❌ Failed",r["message"])
    console.print(rt)

    sc = sum(1 for r in results if r["success"])
    fc = len(results) - sc
    console.print(Panel(f"[green]✅ Success: {sc}[/green]  [red]❌ Failed: {fc}[/red]",
                        border_style="green" if fc==0 else "yellow"))

    # Save manifest
    enrolled = [{"device_id":r["device_id"],"serial":r["serial"],"model":r.get("model"),
                 "enrolled_at":datetime.utcnow().isoformat()} for r in results if r["success"]]
    with open(args.output,"w") as f: json.dump(enrolled,f,indent=2)
    console.print(f"[green]Manifest saved: {args.output}[/green]")

if __name__ == "__main__": main()
