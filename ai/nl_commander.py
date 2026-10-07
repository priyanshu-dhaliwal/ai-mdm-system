import json
from ai.llm_engine import LLMEngine

llm = LLMEngine()

COMMANDS = {
    "lock_screen":"Lock device screen", "wipe_device":"Factory reset (DESTRUCTIVE)",
    "enable_wifi":"Enable WiFi", "disable_wifi":"Disable WiFi",
    "enable_bluetooth":"Enable Bluetooth", "disable_bluetooth":"Disable Bluetooth",
    "get_location":"Get GPS location", "list_apps":"List installed apps",
    "uninstall_app":"Uninstall an app", "push_message":"Push notification",
    "enable_airplane":"Enable airplane mode", "set_volume":"Set volume 0-100",
    "reboot":"Reboot device", "take_screenshot":"Take screenshot",
    "get_battery":"Get battery status", "enforce_policy":"Apply policy group",
}

class NLCommander:
    def __init__(self): self.llm = llm

    def parse_command(self, natural_language: str, device_ids: list) -> dict:
        prompt = f"""Convert this MDM command to JSON.
Available commands: {json.dumps(COMMANDS)}
Input: "{natural_language}"
Devices: {device_ids}
Return ONLY valid JSON:
{{"command":"<key>","devices":["id1"],"params":{{}},"confirmation_required":false,"risk_level":"LOW","explanation":"what it does","reversible":true}}
Rules: wipe_device always needs confirmation_required:true"""
        raw = self.llm.query_sync(prompt)
        return self.llm.extract_json(raw) or {"error":"Parse failed","raw":raw}

    def generate_policy_from_nl(self, description: str) -> dict:
        prompt = f"""Generate MDM policy rule from: "{description}"
Return ONLY valid JSON:
{{"name":"Policy name","group":"default","rule_type":"BLOCK_APP|MIN_BATTERY|WIFI_WHITELIST|etc",
"condition":{{"trigger":"always|battery_below|app_detected|network_change","value":null}},
"action":{{"type":"command","command":"<key>","params":{{}}}},"severity":"LOW|MEDIUM|HIGH"}}"""
        raw = self.llm.query_sync(prompt)
        return self.llm.extract_json(raw) or {"error":"Parse failed","raw":raw}
