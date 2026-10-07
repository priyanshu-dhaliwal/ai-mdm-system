import asyncio
from datetime import datetime
from server.db import SessionLocal, Device, PolicyRule, Alert

class PolicyEngine:
    def __init__(self, ws_manager=None):
        self.ws_manager = ws_manager
        self.default_policies = [
            {"name": "Block Rooted Devices",   "rule_type": "BLOCK_ROOTED",
             "condition": {"trigger": "is_rooted", "value": True},
             "action": {"type": "command", "command": "lock_screen"}, "group": "default"},
            {"name": "Low Battery Warning",    "rule_type": "MIN_BATTERY",
             "condition": {"trigger": "battery_below", "value": 10},
             "action": {"type": "alert", "severity": "MEDIUM"}, "group": "default"},
            {"name": "High Network TX Alert",  "rule_type": "NETWORK_ANOMALY",
             "condition": {"trigger": "network_tx_above", "value": 500},
             "action": {"type": "alert", "severity": "HIGH"}, "group": "default"},
        ]

    async def evaluate_device(self, device: Device, metrics: dict):
        db = SessionLocal()
        violations = []
        try:
            policies = db.query(PolicyRule).filter(
                PolicyRule.active == True,
                PolicyRule.group.in_(["default", device.policy_group])
            ).all()
            for policy in policies:
                violation = self._check_policy(policy, device, metrics)
                if violation:
                    violations.append((policy, violation))
            for policy, reason in violations:
                await self._enforce_policy(policy, device, reason, db)
        finally:
            db.close()
        return violations

    def _check_policy(self, policy, device, metrics):
        c = policy.condition
        trigger, value = c.get("trigger"), c.get("value")
        if trigger == "is_rooted"        and device.is_rooted == value: return "Device is rooted"
        if trigger == "battery_below"    and metrics.get("battery", 100) < value:
            return f"Battery at {metrics.get('battery')}%"
        if trigger == "network_tx_above" and metrics.get("network_tx", 0) > value:
            return f"TX {metrics.get('network_tx')} MB"
        return None

    async def _enforce_policy(self, policy, device, reason, db):
        action = policy.action
        if action.get("type") == "command" and self.ws_manager:
            await self.ws_manager.send_to_device(device.id, {
                "type": "command", "command": action["command"],
                "params": action.get("params", {}), "source": "policy"
            })
        alert = Alert(
            device_id=device.id, device_name=device.name,
            severity=action.get("severity", "MEDIUM"), category="POLICY",
            title=f"Policy Violation: {policy.name}", description=reason
        )
        db.add(alert)
        db.commit()
