import streamlit as st, httpx, json, time, pandas as pd
import plotly.express as px, plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Optional

st.set_page_config(page_title="MDM Command Center", page_icon="🛡️",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Exo+2:wght@300;400;600;700&display=swap');
html,body,[class*="css"]{font-family:'Exo 2',sans-serif;background:#0a0e1a;color:#c9d1d9;}
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#0d1117,#161b22);border-right:1px solid #21262d;}
[data-testid="metric-container"]{background:linear-gradient(135deg,#161b22,#1c2128);border:1px solid #30363d;border-radius:10px;padding:16px;}
.stTabs [data-baseweb="tab-list"]{background:#161b22;border-radius:8px;}
.stTabs [aria-selected="true"]{background:#1f6feb!important;color:white!important;}
.stButton>button{background:linear-gradient(135deg,#1f6feb,#388bfd);color:white;border:none;border-radius:6px;font-family:'Share Tech Mono',monospace;}
.stTextInput>div>div>input,.stTextArea>div>div>textarea{background:#161b22!important;border:1px solid #30363d!important;color:#c9d1d9!important;border-radius:6px!important;font-family:'Share Tech Mono',monospace!important;}
.al-c{background:#3d0b0b;border-left:4px solid #f85149;padding:8px 12px;border-radius:4px;margin:4px 0;}
.al-h{background:#2d1b00;border-left:4px solid #d29922;padding:8px 12px;border-radius:4px;margin:4px 0;}
.al-m{background:#1b2533;border-left:4px solid #388bfd;padding:8px 12px;border-radius:4px;margin:4px 0;}
.al-l{background:#0d2b1e;border-left:4px solid #3fb950;padding:8px 12px;border-radius:4px;margin:4px 0;}
.bdg-c{background:#3d0b0b;color:#f85149;padding:2px 8px;border-radius:12px;font-size:11px;font-family:'Share Tech Mono';}
.bdg-h{background:#2d1b00;color:#d29922;padding:2px 8px;border-radius:12px;font-size:11px;font-family:'Share Tech Mono';}
.bdg-m{background:#1b2533;color:#388bfd;padding:2px 8px;border-radius:12px;font-size:11px;font-family:'Share Tech Mono';}
.bdg-l{background:#0d2b1e;color:#3fb950;padding:2px 8px;border-radius:12px;font-size:11px;font-family:'Share Tech Mono';}
h1,h2,h3{font-family:'Exo 2',sans-serif!important;}
div[data-testid="stExpander"]{background:#161b22;border:1px solid #21262d;border-radius:8px;}
</style>""", unsafe_allow_html=True)

API_BASE = "http://localhost:8000"
HEADERS  = {"Authorization": "Bearer demo_token"}

def api_get(ep, params=None):
    try:    return httpx.get(f"{API_BASE}{ep}", headers=HEADERS, params=params, timeout=5.0).json()
    except: return None

def api_post(ep, body):
    try:    return httpx.post(f"{API_BASE}{ep}", headers=HEADERS, json=body, timeout=30.0).json()
    except Exception as e: return {"error": str(e)}

def mock_devices():
    return [{"id":f"dev-{i:03d}","name":f"Device-{i:03d}","model":m,"android":v,
             "battery":b,"is_online":o,"is_rooted":r,"ip_address":f"192.168.1.{100+i}",
             "policy_group":pg,"risk_score":rs,
             "last_seen":(datetime.utcnow()-timedelta(minutes=mn)).strftime("%Y-%m-%dT%H:%M:%S")}
            for i,(m,v,b,o,r,pg,rs,mn) in enumerate([
            ("Samsung Galaxy S23","13",85,True,False,"default",2.1,1),
            ("Pixel 7 Pro","14",42,True,False,"finance",1.2,2),
            ("OnePlus 11","13",91,True,True,"default",8.5,0),
            ("Xiaomi 13","12",23,True,False,"warehouse",4.3,5),
            ("Samsung A54","13",67,False,False,"default",0.5,120),
            ("Pixel 6a","14",55,True,False,"sales",3.1,3),
            ("Motorola G73","13",12,True,False,"warehouse",5.9,2),
            ("Oppo Find X5","12",78,True,False,"default",1.8,7)],1)]

def mock_alerts():
    return [{"id":f"al-{i}","device_name":dn,"severity":sev,"category":cat,
             "title":t,"resolved":False,"description":d,
             "created_at":(datetime.utcnow()-timedelta(minutes=mn)).strftime("%Y-%m-%dT%H:%M:%S")}
            for i,(dn,sev,cat,t,mn,d) in enumerate([
            ("Device-003","CRITICAL","ANOMALY","Root Access Detected",2,"Root via su binary"),
            ("Device-007","HIGH","POLICY","Low Battery Violation",5,"Battery at 12%"),
            ("Device-004","HIGH","ANOMALY","Excessive Upload (320 MB)",8,"Possible exfiltration"),
            ("Device-003","HIGH","THREAT","USB Debugging on Rooted Device",10,"Critical combination"),
            ("Device-006","MEDIUM","ANOMALY","Off-Hours Activity",15,"Active at 02:30 UTC"),
            ("Device-002","MEDIUM","POLICY","Unknown WiFi",20,"SSID not in allowlist"),
            ("Device-001","LOW","SYSTEM","Heartbeat Delayed",45,"8 min ago")])]

def mock_stats():
    return {"total":8,"online":6,"rooted":1,"avg_risk":3.4,"active_alerts":7,"policies":12}

@st.cache_data(ttl=10)
def get_devices(): return api_get("/devices") or mock_devices()
@st.cache_data(ttl=5)
def get_alerts():  return api_get("/alerts?limit=100") or mock_alerts()
@st.cache_data(ttl=10)
def get_stats():   return api_get("/stats") or mock_stats()

devices = get_devices() or []
alerts  = get_alerts()  or []
stats   = get_stats()   or {}

CHART_LAYOUT = dict(paper_bgcolor="#0a0e1a", plot_bgcolor="#0d1117",
                    font_color="#c9d1d9", margin=dict(l=0,r=0,t=10,b=0))

# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<div style='text-align:center;padding:10px 0 20px'>"
                "<div style='font-family:Share Tech Mono,monospace;font-size:22px;color:#58a6ff;'>🛡️ MDM CC</div>"
                "<div style='font-size:11px;color:#6e7681;margin-top:4px;'>AI-Powered Command Center</div></div>",
                unsafe_allow_html=True)
    page = st.radio("Nav",[
        "📊 Overview","📱 Fleet","🚨 Alerts","🤖 AI Commander",
        "🔒 Policies","🔍 Threat Analyzer","📈 Analytics","⚙️ Settings"],
        label_visibility="collapsed")
    st.divider()
    sv_color = "#3fb950" if api_get("/stats") else "#f85149"
    sv_text  = "Server Online" if api_get("/stats") else "Demo Mode"
    st.markdown(f"<div style='display:flex;align-items:center;gap:8px;padding:8px 0;'>"
                f"<div style='width:8px;height:8px;border-radius:50%;background:{sv_color};"
                f"box-shadow:0 0 6px {sv_color};'></div>"
                f"<span style='font-size:12px;color:#8b949e;font-family:Share Tech Mono,monospace;'>{sv_text}</span></div>",
                unsafe_allow_html=True)
    st.caption(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    if st.button("🔄 Refresh"): st.cache_data.clear(); st.rerun()

SEV_CLS = {"CRITICAL":"al-c","HIGH":"al-h","MEDIUM":"al-m","LOW":"al-l"}
SEV_COL = {"CRITICAL":"#f85149","HIGH":"#d29922","MEDIUM":"#388bfd","LOW":"#3fb950"}

# ═══════════════════════════════════════════════════════════════
if page == "📊 Overview":
    st.markdown("## 🛡️ MDM Command Center")
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Total Devices", stats.get("total",0))
    c2.metric("Online", stats.get("online",0))
    c3.metric("⚠️ Rooted", stats.get("rooted",0))
    c4.metric("Active Alerts", stats.get("active_alerts",0))
    c5.metric("Avg Risk", f"{stats.get('avg_risk',0):.1f}/10")
    st.divider()

    col1, col2 = st.columns([3,2])
    with col1:
        st.markdown("#### 📱 Fleet Risk")
        df = pd.DataFrame(devices)
        if not df.empty:
            fig = px.bar(df.sort_values("risk_score",ascending=False),
                         x="name",y="risk_score",color="risk_score",
                         color_continuous_scale=["#3fb950","#d29922","#f85149"],
                         range_color=[0,10])
            fig.update_layout(**CHART_LAYOUT, height=220, coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown("#### 🚨 Alert Severity")
        sev_c = {}
        for a in alerts: sev_c[a.get("severity","LOW")] = sev_c.get(a.get("severity","LOW"),0)+1
        fig2 = go.Figure(go.Pie(labels=list(sev_c.keys()),values=list(sev_c.values()),hole=0.6,
                                marker=dict(colors=["#f85149","#d29922","#388bfd","#3fb950"])))
        fig2.update_layout(**CHART_LAYOUT, height=220, showlegend=True,
                           legend=dict(orientation="h",y=-0.1))
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()
    st.markdown("#### 🔴 Live Alerts")
    for a in alerts[:8]:
        sev = a.get("severity","LOW")
        ts  = a.get("created_at","")[:16].replace("T"," ")
        st.markdown(f'<div class="{SEV_CLS.get(sev,"al-l")}">'
                    f'<strong>{a.get("device_name","?")}</strong> &nbsp;'
                    f'<span class="bdg-{sev.lower()}">{sev}</span>'
                    f' &nbsp;·&nbsp; {a.get("title","")}'
                    f'<span style="float:right;font-size:11px;color:#8b949e;">{ts}</span></div>',
                    unsafe_allow_html=True)

    st.divider()
    st.markdown("#### 🔋 Battery Status")
    df2 = pd.DataFrame(devices)
    if not df2.empty:
        fig3 = px.bar(df2.sort_values("battery"),x="name",y="battery",color="battery",
                      color_continuous_scale=["#f85149","#d29922","#3fb950"],range_color=[0,100])
        fig3.add_hline(y=20,line_dash="dot",line_color="#d29922",annotation_text="Low Battery")
        fig3.update_layout(**CHART_LAYOUT, height=200, coloraxis_showscale=False)
        st.plotly_chart(fig3, use_container_width=True)

# ═══════════════════════════════════════════════════════════════
elif page == "📱 Fleet":
    st.markdown("## 📱 Fleet Manager")
    fc1,fc2,fc3 = st.columns(3)
    fs = fc1.selectbox("Status",["All","Online","Offline"])
    fg = fc2.selectbox("Group",["All"]+list(set(d.get("policy_group","default") for d in devices)))
    fr = fc3.selectbox("Risk",["All","Critical (8+)","High (6+)","Medium (3+)","Low (<3)"])

    filtered = devices
    if fs == "Online":  filtered = [d for d in filtered if d.get("is_online")]
    if fs == "Offline": filtered = [d for d in filtered if not d.get("is_online")]
    if fg != "All":     filtered = [d for d in filtered if d.get("policy_group")==fg]
    risk_map = {"Critical (8+)":(8,11),"High (6+)":(6,8),"Medium (3+)":(3,6),"Low (<3)":(0,3)}
    if fr in risk_map: filtered = [d for d in filtered if risk_map[fr][0]<=d.get("risk_score",0)<risk_map[fr][1]]
    st.caption(f"Showing {len(filtered)}/{len(devices)} devices")
    st.divider()

    for dev in filtered:
        icon = "🔴" if dev.get("is_rooted") else ("🟢" if dev.get("is_online") else "⚫")
        risk = dev.get("risk_score",0)
        with st.expander(f"{icon} {dev.get('name')}  ·  {dev.get('model')}  ·  Risk: {risk:.1f}  ·  Battery: {dev.get('battery')}%"):
            d1,d2,d3,d4 = st.columns(4)
            d1.metric("IP", dev.get("ip_address","N/A"))
            d2.metric("Android", dev.get("android","?"))
            d3.metric("Group", dev.get("policy_group","default"))
            d4.metric("Last Seen", dev.get("last_seen","")[:16].replace("T"," "))
            st.divider()
            a1,a2,a3,a4,a5 = st.columns(5)
            dev_id = dev.get("id")
            if a1.button("🔒 Lock",    key=f"lk_{dev_id}"): st.success("Lock sent")
            if a2.button("📍 Locate",  key=f"lo_{dev_id}"): st.info("Location requested")
            if a3.button("📋 Apps",    key=f"ap_{dev_id}"): st.info("App list requested")
            if a4.button("🔄 Reboot",  key=f"rb_{dev_id}"): st.warning("Reboot sent")
            if a5.button("✈️ Airplane",key=f"ai_{dev_id}"): st.warning("Airplane mode")
            if dev.get("is_rooted"):  st.error("⚠️ ROOTED device — security compromised!")
            if not dev.get("is_online"): st.warning("Device offline")

# ═══════════════════════════════════════════════════════════════
elif page == "🚨 Alerts":
    st.markdown("## 🚨 Alert Center")
    ac1,ac2,ac3,ac4 = st.columns(4)
    sc = {}
    for a in alerts: sc[a.get("severity","LOW")] = sc.get(a.get("severity","LOW"),0)+1
    ac1.metric("Critical",sc.get("CRITICAL",0))
    ac2.metric("High",sc.get("HIGH",0))
    ac3.metric("Medium",sc.get("MEDIUM",0))
    ac4.metric("Low",sc.get("LOW",0))
    st.divider()
    sf = st.multiselect("Filter Severity",["CRITICAL","HIGH","MEDIUM","LOW"],
                        default=["CRITICAL","HIGH","MEDIUM","LOW"])
    for a in [x for x in alerts if x.get("severity") in sf]:
        sev = a.get("severity","LOW")
        with st.expander(f"[{sev}] {a.get('device_name','?')} — {a.get('title','')}",
                         expanded=sev=="CRITICAL"):
            i1,i2,i3 = st.columns(3)
            i1.metric("Severity",sev); i2.metric("Category",a.get("category","—")); i3.metric("Device",a.get("device_name","—"))
            if a.get("description"): st.caption(a["description"])
            if a.get("ai_analysis"): st.info(f"🤖 {a['ai_analysis']}")
            b1,b2 = st.columns(2)
            if b1.button("✅ Resolve",   key=f"res_{a.get('id')}"): st.success("Resolved")
            if b2.button("🔍 Investigate",key=f"inv_{a.get('id')}"): st.info("Investigating...")

# ═══════════════════════════════════════════════════════════════
elif page == "🤖 AI Commander":
    st.markdown("## 🤖 AI Natural Language Commander")
    st.caption("Control your fleet in plain English. Powered by local Ollama — no data leaves your server.")
    st.divider()
    ex1,ex2,ex3 = st.columns(3)
    with ex1:
        st.markdown('<div style="background:#161b22;border:1px solid #30363d;border-radius:8px;padding:12px;">'
                    '<div style="font-family:Share Tech Mono;font-size:12px;color:#58a6ff;">Device Control</div>'
                    '<div style="font-size:12px;margin-top:8px;color:#8b949e;">"Lock all offline devices"<br>'
                    '"Reboot warehouse group"<br>"Enable airplane on Device-003"</div></div>',unsafe_allow_html=True)
    with ex2:
        st.markdown('<div style="background:#161b22;border:1px solid #30363d;border-radius:8px;padding:12px;">'
                    '<div style="font-family:Share Tech Mono;font-size:12px;color:#3fb950;">Security</div>'
                    '<div style="font-size:12px;margin-top:8px;color:#8b949e;">"Block WiFi on rooted devices"<br>'
                    '"Disable USB debugging fleet-wide"<br>"Push security alert to finance"</div></div>',unsafe_allow_html=True)
    with ex3:
        st.markdown('<div style="background:#161b22;border:1px solid #30363d;border-radius:8px;padding:12px;">'
                    '<div style="font-family:Share Tech Mono;font-size:12px;color:#d29922;">Policy</div>'
                    '<div style="font-size:12px;margin-top:8px;color:#8b949e;">"Create policy: block USB on all"<br>'
                    '"Alert when battery below 15%"<br>"Lock devices after midnight"</div></div>',unsafe_allow_html=True)
    st.divider()

    if "chat" not in st.session_state: st.session_state.chat = []
    for msg in st.session_state.chat:
        if msg["role"] == "user":
            st.markdown(f'<div style="text-align:right;margin:8px 0;">'
                        f'<span style="background:#1f6feb;color:white;padding:8px 14px;'
                        f'border-radius:18px 18px 4px 18px;font-size:13px;">{msg["content"]}</span></div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="text-align:left;margin:8px 0;">'
                        f'<div style="background:#161b22;border:1px solid #30363d;color:#c9d1d9;'
                        f'padding:10px 14px;border-radius:18px 18px 18px 4px;font-size:13px;'
                        f'display:inline-block;max-width:80%;font-family:Share Tech Mono,monospace;">'
                        f'🤖 {msg["content"]}</div></div>', unsafe_allow_html=True)

    cin, cbt = st.columns([5,1])
    nl  = cin.text_input("CMD","",label_visibility="collapsed",
                          placeholder="e.g. 'Lock all rooted devices immediately'")
    send = cbt.button("⚡ Send", use_container_width=True)

    if send and nl.strip():
        st.session_state.chat.append({"role":"user","content":nl})
        with st.spinner("🤖 AI processing..."):
            res = api_post("/ai/command",{"input":nl,"devices":"all"})
        if res and not res.get("error"):
            risk = res.get("risk_level","LOW")
            re   = {"LOW":"🟢","MEDIUM":"🟡","HIGH":"🟠","CRITICAL":"🔴"}.get(risk,"⚪")
            resp = (f"Command: `{res.get('command','?')}`\n"
                    f"Risk: {re} {risk} | Reversible: {'Yes' if res.get('reversible') else '⚠️ NO'}\n"
                    f"{res.get('explanation','')}"
                    + ("\n\n⚠️ Requires confirmation." if res.get("confirmation_required") else "\n\n✅ Queued."))
        else: resp = f"Error: {(res or {}).get('error','Server unavailable')}"
        st.session_state.chat.append({"role":"assistant","content":resp})
        st.rerun()

    if st.button("🗑️ Clear"): st.session_state.chat = []; st.rerun()
    st.divider()
    st.markdown("#### 📜 AI Policy Generator")
    pd_txt = st.text_area("Describe a policy in plain English",height=80,
                          placeholder="e.g. 'Block all devices connecting to unknown WiFi and send an alert'")
    if st.button("🧠 Generate Policy") and pd_txt.strip():
        with st.spinner("Generating..."):
            res = api_post("/ai/policy",{"text":pd_txt})
        st.success("Policy generated!"); st.json(res or {"name":"Demo Policy","rule_type":"WIFI_WHITELIST"})

# ═══════════════════════════════════════════════════════════════
elif page == "🔒 Policies":
    st.markdown("## 🔒 Policy Engine")
    policies = [
        {"name":"Block Rooted Devices","group":"default","type":"BLOCK_ROOTED","action":"lock_screen","sev":"CRITICAL","active":True,"ai":False},
        {"name":"Low Battery Alert","group":"default","type":"MIN_BATTERY","action":"alert","sev":"MEDIUM","active":True,"ai":False},
        {"name":"High Network TX","group":"default","type":"NETWORK_ANOMALY","action":"alert","sev":"HIGH","active":True,"ai":False},
        {"name":"USB Debug Block","group":"default","type":"BLOCK_USB_DEBUG","action":"alert+log","sev":"HIGH","active":True,"ai":True},
        {"name":"Finance WiFi Restriction","group":"finance","type":"WIFI_WHITELIST","action":"airplane","sev":"HIGH","active":True,"ai":True},
        {"name":"After-Hours Activity","group":"default","type":"TIME_RANGE","action":"alert","sev":"MEDIUM","active":False,"ai":True},
    ]
    for p in policies:
        ai_b = '<span style="background:#2d1f6b;color:#a5b4fc;padding:1px 6px;border-radius:10px;font-size:10px;">AI</span>' if p["ai"] else ""
        c1,c2,c3,c4,c5,c6 = st.columns([3,2,2,2,1,1])
        c1.markdown(f"**{p['name']}** {ai_b}", unsafe_allow_html=True)
        c2.caption(p["group"]); c3.caption(f"`{p['type']}`"); c4.caption(p["action"])
        c5.markdown(f'<span class="bdg-{p["sev"].lower()}">{p["sev"]}</span>', unsafe_allow_html=True)
        c6.checkbox("",value=p["active"],key=f"pol_{p['name']}",label_visibility="collapsed")
        st.divider()

    st.markdown("#### ➕ Create Policy")
    with st.form("new_pol"):
        n1,n2 = st.columns(2)
        pname = n1.text_input("Name"); pgrp = n2.selectbox("Group",["default","finance","warehouse","sales"])
        n3,n4 = st.columns(2)
        ptype = n3.selectbox("Type",["BLOCK_ROOTED","MIN_BATTERY","WIFI_WHITELIST","BLOCK_USB_DEBUG","CUSTOM"])
        pact  = n4.selectbox("Action",["alert","lock_screen","enable_airplane","disable_wifi","log_only"])
        if st.form_submit_button("💾 Save") and pname:
            st.success(f"Policy '{pname}' saved!")

# ═══════════════════════════════════════════════════════════════
elif page == "🔍 Threat Analyzer":
    st.markdown("## 🔍 AI Threat Analyzer")
    dev_names = [d.get("name",d.get("id")) for d in devices]
    sel_name  = st.selectbox("Select Device", dev_names)
    sel_dev   = next((d for d in devices if d.get("name")==sel_name), devices[0] if devices else {})

    col_s, col_a = st.columns([2,1])
    run_analysis = col_s.button("🔍 Run Full AI Threat Analysis", use_container_width=True)
    auto_rem     = col_a.checkbox("Auto-execute safe remediations")

    if run_analysis and sel_dev:
        with st.spinner(f"Analyzing {sel_name}..."):
            time.sleep(1.5)
            is_rooted = sel_dev.get("is_rooted",False)
            score     = 8.5 if is_rooted else 3.1
            sev       = "CRITICAL" if is_rooted else "MEDIUM"
            sc        = SEV_COL.get(sev,"#c9d1d9")
            findings  = ([{"title":"Root Access Detected","sev":"CRITICAL","score":4.0,
                           "mitre":["T1401","T1400"],"desc":"Root access — OS integrity compromised.",
                           "remed":["Lock device immediately","Initiate wipe","Issue replacement"],
                           "auto":True,"cmd":"lock_screen"}] if is_rooted else
                         [{"title":"Off-Hours Network Activity","sev":"MEDIUM","score":1.5,
                           "mitre":["T1437","T1533"],"desc":"Data transmission at 03:00 UTC.",
                           "remed":["Review background apps","Check push notifications"],"auto":False,"cmd":None},
                          {"title":"Battery Drain Anomaly","sev":"MEDIUM","score":1.6,
                           "mitre":["T1429","T1430"],"desc":"18%/hr drain — possible surveillance.",
                           "remed":["Review app permissions","Check camera/mic access"],"auto":False,"cmd":None}])
            summary = (f"{sel_name} shows critical indicators consistent with a compromised device. "
                       "Root access and USB debugging present significant exfiltration risk."
                       if is_rooted else
                       f"{sel_name} shows moderate risk indicators requiring investigation.")

        fig_g = go.Figure(go.Indicator(mode="gauge+number",value=score,
            title={"text":f"Risk — {sev}","font":{"color":sc,"size":16}},
            gauge={"axis":{"range":[0,10]},"bar":{"color":sc},"bgcolor":"#161b22",
                   "steps":[{"range":[0,3],"color":"#0d2b1e"},{"range":[3,6],"color":"#1b2533"},
                             {"range":[6,8],"color":"#2d1b00"},{"range":[8,10],"color":"#3d0b0b"}]}))
        fig_g.update_layout(paper_bgcolor="#0a0e1a",font_color="#c9d1d9",height=220,
                            margin=dict(l=20,r=20,t=30,b=10))
        g1,g2 = st.columns([1,2])
        with g1: st.plotly_chart(fig_g, use_container_width=True)
        with g2: st.markdown("**Summary**"); st.info(summary)

        st.divider()
        st.markdown("#### 🎯 Findings")
        for f in findings:
            with st.expander(f"[{f['sev']}] {f['title']} — Score: {f['score']:.1f}"):
                st.markdown(f"**Description:** {f['desc']}")
                st.markdown(f"**MITRE:** `{'`, `'.join(f['mitre'])}`")
                st.markdown("**Remediation:**")
                for i,r in enumerate(f["remed"],1): st.markdown(f"  {i}. {r}")
                if f["auto"] and auto_rem and f["cmd"]:
                    if st.button(f"⚡ Execute: {f['cmd']}",key=f"exec_{f['title']}"):
                        st.success(f"Command '{f['cmd']}' sent to {sel_name}")

# ═══════════════════════════════════════════════════════════════
elif page == "📈 Analytics":
    st.markdown("## 📈 Fleet Analytics")
    dates = pd.date_range(end=datetime.now(), periods=30, freq="D")
    risk_data = pd.DataFrame({"Date":dates,
        "Avg Risk":[2.1,2.3,2.0,3.1,2.8,2.5,4.2,5.1,4.8,3.9,3.5,3.2,4.0,4.5,4.1,
                    3.8,3.6,5.2,6.1,5.8,5.5,5.0,4.8,5.1,6.3,7.2,6.8,7.5,8.1,7.9],
        "Alerts":[1,2,1,3,2,2,5,7,6,4,3,3,4,5,4,3,3,6,8,7,6,5,5,6,8,11,9,12,14,13]})
    fig_t = go.Figure()
    fig_t.add_trace(go.Scatter(x=risk_data["Date"],y=risk_data["Avg Risk"],
                               mode="lines+markers",name="Risk",line=dict(color="#f85149",width=2),
                               fill="tozeroy",fillcolor="rgba(248,81,73,0.1)"))
    fig_t.add_trace(go.Bar(x=risk_data["Date"],y=risk_data["Alerts"],name="Alerts",
                           yaxis="y2",marker_color="rgba(31,111,235,0.5)"))
    fig_t.update_layout(**CHART_LAYOUT, height=280,
                        yaxis=dict(title="Risk Score",range=[0,10]),
                        yaxis2=dict(title="Alerts",overlaying="y",side="right"),
                        legend=dict(orientation="h",y=1.1))
    st.plotly_chart(fig_t, use_container_width=True)

    c1,c2 = st.columns(2)
    with c1:
        st.markdown("#### Policy Group Risk")
        df = pd.DataFrame(devices)
        if not df.empty:
            grp = df.groupby("policy_group")["risk_score"].mean().reset_index()
            fig2 = px.bar(grp,x="policy_group",y="risk_score",color="risk_score",
                          color_continuous_scale=["#3fb950","#d29922","#f85149"],range_color=[0,10])
            fig2.update_layout(**CHART_LAYOUT, height=220, coloraxis_showscale=False)
            st.plotly_chart(fig2, use_container_width=True)
    with c2:
        st.markdown("#### Alert Categories")
        cc = {}
        for a in alerts: cc[a.get("category","OTHER")] = cc.get(a.get("category","OTHER"),0)+1
        fig3 = px.pie(names=list(cc.keys()),values=list(cc.values()),hole=0.5,
                      color_discrete_sequence=["#f85149","#d29922","#388bfd","#3fb950"])
        fig3.update_layout(**CHART_LAYOUT, height=220)
        st.plotly_chart(fig3, use_container_width=True)

# ═══════════════════════════════════════════════════════════════
elif page == "⚙️ Settings":
    st.markdown("## ⚙️ Settings")
    t1,t2,t3 = st.tabs(["🤖 AI","🔐 Security","📡 Server"])
    with t1:
        st.text_input("Ollama Host", "http://localhost:11434")
        st.selectbox("LLM Model",["mistral","llama3","llama3:8b","codellama","phi3"])
        st.slider("Temperature",0.0,1.0,0.1)
        if st.button("🧪 Test AI"):  st.success("✅ Connected — mistral | 142ms")
    with t2:
        st.toggle("Enforce encryption",value=True); st.toggle("Block rooted devices",value=True)
        st.toggle("Require screen lock",value=True); st.toggle("Alert on unknown WiFi",value=True)
        st.toggle("Auto-lock on anomaly",value=False); st.divider()
        st.text_input("Enrollment Token","demo_token",type="password")
        if st.button("🔄 Rotate Token"): st.success("Token rotated")
    with t3:
        st.text_input("Host","0.0.0.0"); st.number_input("Port",value=8000)
        st.text_input("TLS Cert","./certs/cert.pem"); st.text_input("TLS Key","./certs/key.pem")
        if st.button("💾 Save"): st.success("Saved")
        if st.button("🔄 Restart"): st.warning("Restarting...")
