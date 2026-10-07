import json
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional
from ai.llm_engine import LLMEngine

llm = LLMEngine()

MITRE_MOBILE = {
    "T1437":"Application Layer Protocol","T1533":"Data from Local System",
    "T1407":"Download New Code at Runtime","T1430":"Location Tracking",
    "T1513":"Screen Capture","T1422":"System Network Configuration Discovery",
    "T1398":"Boot or Logon Initialization Scripts","T1400":"Modify System Partition",
    "T1401":"Device Administrator Permissions","T1406":"Obfuscated Files or Information",
    "T1412":"Capture SMS Messages","T1414":"Capture Clipboard Data",
    "T1418":"Software Discovery","T1429":"Capture Audio","T1432":"Access Contact List",
    "T1433":"Access Call Log","T1507":"Network Information Discovery",
    "T1512":"Video Capture","T1516":"Input Injection","T1517":"Access Notifications",
    "T1521":"Encrypted Channel","T1523":"Evade Analysis Environment",
    "T1461":"Lockscreen Bypass",
}

@dataclass
class ThreatFinding:
    threat_id: str; title: str; severity: str; score: float
    mitre_ids: list = field(default_factory=list)
    cve_ids: list   = field(default_factory=list)
    description: str = ""
    evidence: dict  = field(default_factory=dict)
    remediation: list = field(default_factory=list)
    auto_actionable: bool = False
    suggested_cmd: Optional[str] = None
    detected_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

@dataclass
class ThreatReport:
    device_id: str; device_name: str
    analysis_time: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    overall_score: float = 0.0; overall_severity: str = "LOW"
    findings: list = field(default_factory=list)
    mitre_summary: dict = field(default_factory=dict)
    executive_summary: str = ""; recommended_actions: list = field(default_factory=list)
    ai_narrative: str = ""

class ThreatAnalyzer:
    def __init__(self): self.llm = llm

    def analyze(self, device_id, device_name, metrics, app_list=None) -> ThreatReport:
        report   = ThreatReport(device_id=device_id, device_name=device_name)
        findings = (self._check_root(metrics) + self._check_developer_flags(metrics) +
                    self._check_network(metrics) + self._check_battery(metrics) +
                    self._check_apps(app_list or []) + self._check_behavioral(metrics) +
                    self._check_off_hours(metrics))
        report.findings = [self._ai_enrich(f, device_name) for f in findings]
        report.overall_score    = min(10.0, round(sum(f.score for f in report.findings), 2))
        report.overall_severity = self._score_to_sev(report.overall_score)
        all_mitre = [m for f in report.findings for m in f.mitre_ids]
        report.mitre_summary = {m: MITRE_MOBILE.get(m,"Unknown") for m in set(all_mitre)}
        if findings:
            s = self._ai_summary(report)
            report.executive_summary   = s.get("executive_summary","")
            report.recommended_actions = s.get("recommended_actions",[])
            report.ai_narrative        = s.get("narrative","")
        return report

    def _check_root(self, m):
        if not m.get("is_rooted"): return []
        return [ThreatFinding("ROOT","Device Rooted","CRITICAL",4.0,
                              ["T1401","T1400"],"Root access — OS integrity compromised",
                              {"is_rooted":True},[],True,"lock_screen")]

    def _check_developer_flags(self, m):
        out = []
        if m.get("usb_debugging"):
            out.append(ThreatFinding("USB_DEBUG","USB Debugging Enabled","HIGH",2.5,
                       ["T1406","T1516"],"ADB shell access from any connected host",{"usb_debugging":True}))
        if m.get("developer_mode"):
            out.append(ThreatFinding("DEV_MODE","Developer Mode Enabled","HIGH",2.5,
                       ["T1406"],"Exposes settings that bypass security controls",{"developer_mode":True}))
        if m.get("play_protect_disabled"):
            out.append(ThreatFinding("PLAY_PROTECT_OFF","Play Protect Disabled","HIGH",2.0,
                       ["T1407","T1523"],"Primary anti-malware scanner disabled",{"play_protect":False}))
        return out

    def _check_network(self, m):
        out = []
        if m.get("network_tx",0) > 200:
            sev = "CRITICAL" if m["network_tx"] > 500 else "HIGH"
            out.append(ThreatFinding("HIGH_NET_TX",f"Excessive Upload ({m['network_tx']:.0f} MB)",
                       sev, min(3.5, m["network_tx"]/200), ["T1437","T1533"],
                       "Possible data exfiltration",{"network_tx": m["network_tx"]},
                       [],m["network_tx"]>500,"disable_wifi"))
        wifi, allowed = m.get("wifi_ssid",""), m.get("allowed_ssids",[])
        if wifi and allowed and wifi not in allowed:
            out.append(ThreatFinding("UNKNOWN_WIFI",f"Unauthorised WiFi: {wifi}","HIGH",2.0,
                       ["T1437"],f"SSID '{wifi}' not in allowed list",{"ssid":wifi},
                       [],True,"enable_airplane"))
        return out

    def _check_battery(self, m):
        if m.get("battery_drain_rate",0) > 15:
            return [ThreatFinding("BATTERY_DRAIN",f"Rapid Drain ({m['battery_drain_rate']:.1f}%/hr)",
                    "MEDIUM",1.5,["T1429","T1430"],"Background surveillance or crypto-mining",
                    {"drain_rate":m["battery_drain_rate"]})]
        return []

    def _check_apps(self, apps):
        out = []
        known_bad = {"com.android.phonetool","com.phonetool.android"}
        spy_patterns = ["com.spy","com.rat","com.keylog","com.track","com.monitor","com.hidden"]
        for app in apps:
            pkg = app.get("package","").lower()
            name = app.get("name", pkg)
            if pkg in known_bad:
                out.append(ThreatFinding(f"MALWARE_{pkg[:20]}",f"Known Malware: {name}",
                           "CRITICAL",4.0,["T1407"],"Matches known malware signature",{"package":pkg},
                           [],True,f"uninstall_app:{pkg}"))
            elif any(pkg.startswith(p) for p in spy_patterns):
                out.append(ThreatFinding(f"SUSPECT_{pkg[:20]}",f"Suspicious Package: {name}",
                           "HIGH",2.5,["T1407"],"Matches surveillance patterns",{"package":pkg}))
            elif app.get("sideloaded"):
                out.append(ThreatFinding(f"SIDELOAD_{pkg[:20]}",f"Sideloaded App: {name}",
                           "MEDIUM",1.5,["T1407"],"Installed outside Play Store",{"package":pkg}))
        return out

    def _check_behavioral(self, m):
        out = []
        if m.get("screen_recording_active"):
            out.append(ThreatFinding("SCREEN_REC","Active Screen Recording","CRITICAL",3.5,
                       ["T1513"],"Possible data theft in progress",{},[]  ,True,"lock_screen"))
        if m.get("accessibility_service_abuse"):
            out.append(ThreatFinding("ACC_ABUSE","Accessibility Service Misuse","CRITICAL",3.5,
                       ["T1516","T1517"],"Common spyware technique",{},[]  ,True,"lock_screen"))
        if m.get("failed_unlock_attempts",0) >= 5:
            out.append(ThreatFinding("BRUTE_FORCE",f"Failed Unlocks ({m['failed_unlock_attempts']})",
                       "MEDIUM",1.5,["T1461"],"Possible physical brute force",
                       {"attempts":m["failed_unlock_attempts"]}))
        if m.get("sms_sent_count",0) > 50:
            out.append(ThreatFinding("SMS_SPIKE",f"SMS Spike ({m['sms_sent_count']})",
                       "HIGH",2.5,["T1412"],"SMS trojan or premium fraud",
                       {"count":m["sms_sent_count"]}))
        return out

    def _check_off_hours(self, m):
        hour = datetime.utcnow().hour
        if (m.get("screen_on") or m.get("network_tx",0) > 50) and (hour < 6 or hour > 22):
            return [ThreatFinding("OFF_HOURS",f"Activity at {hour:02d}:00 UTC","MEDIUM",1.0,
                    ["T1533"],"Significant activity outside business hours",{"hour":hour})]
        return []

    def _ai_enrich(self, f: ThreatFinding, device_name: str) -> ThreatFinding:
        prompt = f"""Enrich this MDM finding with expert context. Return ONLY valid JSON:
Finding: {f.title} | Severity: {f.severity} | MITRE: {f.mitre_ids}
{{"additional_mitre_ids":[],"cve_ids":[],"refined_description":"2 sentence expert description",
"remediation_steps":["Step 1","Step 2","Step 3"],"confidence":"HIGH|MEDIUM|LOW",
"threat_actor_likelihood":"APT|CRIMINAL|INSIDER|ACCIDENTAL"}}"""
        try:
            raw = self.llm.query_sync(prompt)
            e   = self.llm.extract_json(raw)
            if e:
                f.mitre_ids  = list(set(f.mitre_ids + e.get("additional_mitre_ids",[])))
                f.cve_ids    = e.get("cve_ids",[])
                f.description= e.get("refined_description", f.description)
                f.remediation= e.get("remediation_steps",[])
        except: pass
        return f

    def _ai_summary(self, report: ThreatReport) -> dict:
        prompt = f"""Generate executive threat report. Return ONLY valid JSON:
Device: {report.device_name} | Score: {report.overall_score}/10 | Severity: {report.overall_severity}
Findings: {[{"title":f.title,"sev":f.severity} for f in report.findings]}
{{"executive_summary":"3-sentence non-technical summary","narrative":"2-3 sentence technical narrative",
"recommended_actions":[{{"priority":1,"action":"specific action","timeframe":"Immediate|24h|7 days","owner":"MDM Admin"}}]}}"""
        try:
            raw = self.llm.query_sync(prompt)
            return self.llm.extract_json(raw) or {}
        except: return {}

    @staticmethod
    def _score_to_sev(score):
        if score >= 8: return "CRITICAL"
        if score >= 6: return "HIGH"
        if score >= 3: return "MEDIUM"
        if score >= 1: return "LOW"
        return "INFO"

    def to_dict(self, r: ThreatReport) -> dict:
        return {"device_id":r.device_id,"device_name":r.device_name,
                "analysis_time":r.analysis_time,"overall_score":r.overall_score,
                "overall_severity":r.overall_severity,
                "findings":[asdict(f) for f in r.findings],
                "mitre_summary":r.mitre_summary,"executive_summary":r.executive_summary,
                "recommended_actions":r.recommended_actions,"ai_narrative":r.ai_narrative}
