from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import json
from server.db import get_db, Device, Alert, PolicyRule, DeviceMetrics, init_db
from ai.nl_commander import NLCommander
from ai.anomaly_detector import AnomalyDetector
from ai.threat_analyzer import ThreatAnalyzer
from server.policy_engine import PolicyEngine
from sqlalchemy.orm import Session

app         = FastAPI(title="MDM Server", version="2.0")
commander   = NLCommander()
detector    = AnomalyDetector()
analyzer    = ThreatAnalyzer()

class ConnectionManager:
    def __init__(self):
        self.device_connections: dict = {}

    async def connect(self, device_id: str, ws: WebSocket):
        await ws.accept()
        self.device_connections[device_id] = ws

    def disconnect(self, device_id: str):
        self.device_connections.pop(device_id, None)

    async def send_to_device(self, device_id: str, message: dict):
        ws = self.device_connections.get(device_id)
        if ws:
            await ws.send_json(message)

    async def broadcast(self, message: dict):
        for dev_id, ws in list(self.device_connections.items()):
            try: await ws.send_json(message)
            except: self.disconnect(dev_id)

manager       = ConnectionManager()
policy_engine = PolicyEngine(ws_manager=manager)

app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

@app.websocket("/ws/device/{device_id}")
async def device_ws(ws: WebSocket, device_id: str, db: Session = Depends(get_db)):
    await manager.connect(device_id, ws)
    try:
        device = db.query(Device).filter(Device.id == device_id).first()
        if device:
            device.is_online = True; db.commit()
        while True:
            data = await ws.receive_json()
            await handle_device_message(device_id, data, db)
    except WebSocketDisconnect:
        manager.disconnect(device_id)
        device = db.query(Device).filter(Device.id == device_id).first()
        if device:
            device.is_online = False; db.commit()

async def handle_device_message(device_id: str, data: dict, db: Session):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device: return
    if data.get("type") == "heartbeat":
        device.last_seen  = datetime.utcnow()
        device.battery    = data.get("battery", device.battery)
        device.is_rooted  = data.get("is_rooted", False)
        device.ip_address = data.get("ip", device.ip_address)
        db.commit()
        metrics = {"battery": data.get("battery",0), "cpu_usage": data.get("cpu",0),
                   "ram_usage": data.get("ram",0), "network_rx": data.get("net_rx",0),
                   "network_tx": data.get("net_tx",0), "is_rooted": data.get("is_rooted",False),
                   "app_count": data.get("app_count",0)}
        anomaly = detector.detect(device_id, metrics)
        if anomaly.get("anomaly"):
            alert = Alert(device_id=device_id, device_name=device.name,
                          severity="HIGH", category="ANOMALY",
                          title="Behavioral Anomaly Detected",
                          description=anomaly.get("ai_explanation",""),
                          ai_analysis=anomaly.get("ai_explanation",""))
            db.add(alert); db.commit()
        await policy_engine.evaluate_device(device, metrics)

@app.get("/devices")
def get_devices(db: Session = Depends(get_db)):
    return db.query(Device).all()

@app.get("/alerts")
def get_alerts(limit: int = 50, db: Session = Depends(get_db)):
    return db.query(Alert).order_by(Alert.created_at.desc()).limit(limit).all()

@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    devices = db.query(Device).all()
    return {"total": len(devices), "online": sum(1 for d in devices if d.is_online),
            "rooted": sum(1 for d in devices if d.is_rooted),
            "avg_risk": sum(d.risk_score for d in devices) / max(len(devices),1),
            "active_alerts": db.query(Alert).filter(Alert.resolved==False).count(),
            "policies": db.query(PolicyRule).filter(PolicyRule.active==True).count()}

class NLCommand(BaseModel):
    input: str
    devices: str = "all"

@app.post("/ai/command")
async def ai_command(cmd: NLCommand, db: Session = Depends(get_db)):
    devices = db.query(Device).filter(Device.is_online==True).all()
    parsed  = commander.parse_command(cmd.input, [d.id for d in devices])
    if not parsed.get("confirmation_required") and not parsed.get("error"):
        if parsed.get("risk_level") in ["LOW","MEDIUM"]:
            for dev_id in parsed.get("devices",[]):
                await manager.send_to_device(dev_id, {
                    "type": "command", "command": parsed["command"],
                    "params": parsed.get("params",{}), "source": "ai_nl"})
    return parsed

@app.post("/ai/policy")
async def create_ai_policy(description: dict, db: Session = Depends(get_db)):
    policy_data = commander.generate_policy_from_nl(description["text"])
    if "error" not in policy_data:
        policy = PolicyRule(name=policy_data.get("name","AI Policy"),
                            group=policy_data.get("group","default"),
                            rule_type=policy_data.get("rule_type","CUSTOM"),
                            condition=policy_data.get("condition",{}),
                            action=policy_data.get("action",{}), ai_generated=True)
        db.add(policy); db.commit()
    return policy_data

@app.post("/ai/threat-analyze")
async def threat_analyze(payload: dict, db: Session = Depends(get_db)):
    report = analyzer.analyze(
        device_id=payload.get("device_id",""),
        device_name=payload.get("device_name","Unknown"),
        metrics=payload.get("metrics",{}),
        app_list=payload.get("app_list",[]))
    return analyzer.to_dict(report)

@app.on_event("startup")
def startup(): init_db()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server.main:app", host="0.0.0.0", port=8000, reload=True)
