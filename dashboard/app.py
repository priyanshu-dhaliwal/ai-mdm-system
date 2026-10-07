from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Static, Input, Label, DataTable, RichLog
from textual.binding import Binding
from rich.text import Text
import httpx, asyncio

API_BASE = "http://localhost:8000"
HEADERS  = {"Authorization": "Bearer demo_token"}

BANNER = """[bold red]
 ██╗  ██╗██████╗ ███╗   ███╗
 ██║ ██╔╝██╔══██╗████╗ ████║
 █████╔╝ ██║  ██║██╔████╔██║
 ██╔═██╗ ██║  ██║██║╚██╔╝██║
 ██║  ██╗██████╔╝██║ ╚═╝ ██║
 ╚═╝  ╚═╝╚═════╝ ╚═╝     ╚═╝
  AI-MDM v2.0 | Kali Linux[/bold red]"""

class DeviceTable(Static):
    def compose(self) -> ComposeResult:
        yield DataTable(id="dt")

    def on_mount(self):
        t = self.query_one(DataTable)
        t.add_columns("Device","Status","Battery","CPU","IP","Group","Risk","Last Seen")
        self.set_interval(5, self.fetch_data)

    async def fetch_data(self):
        try:
            async with httpx.AsyncClient() as c:
                r = await c.get(f"{API_BASE}/devices", headers=HEADERS, timeout=4)
                devices = r.json()
            t = self.query_one(DataTable); t.clear()
            for d in devices:
                risk = d.get("risk_score",0)
                rc   = "red" if risk>7 else "yellow" if risk>4 else "green"
                t.add_row(
                    ("⚠️ " if d.get("is_rooted") else "") + d["name"],
                    "🟢" if d["is_online"] else "🔴",
                    f"{d['battery']}%", f"{d.get('cpu',0):.0f}%",
                    d.get("ip_address","—"), d.get("policy_group","default"),
                    Text(f"{risk:.1f}", style=rc), d.get("last_seen","")[:16])
        except: pass

class AlertPanel(Static):
    def compose(self) -> ComposeResult:
        yield RichLog(id="al", highlight=True, markup=True)

    def on_mount(self):
        self.set_interval(3, self.fetch_data)

    async def fetch_data(self):
        try:
            async with httpx.AsyncClient() as c:
                r = await c.get(f"{API_BASE}/alerts?limit=20", headers=HEADERS, timeout=4)
                alerts = r.json()
            log = self.query_one(RichLog); log.clear()
            for a in reversed(alerts):
                sev = a.get("severity","LOW")
                col = {"CRITICAL":"bold red","HIGH":"red","MEDIUM":"yellow","LOW":"green"}.get(sev,"white")
                ts  = a.get("created_at","")[:16]
                log.write(f"[{col}][{sev}][/{col}] {ts} | [bold]{a.get('device_name')}[/bold] | {a.get('title')}")
        except: pass

class StatsPanel(Static):
    def compose(self) -> ComposeResult:
        yield Static(id="sc")

    def on_mount(self):
        self.set_interval(10, self.fetch_data)

    async def fetch_data(self):
        try:
            async with httpx.AsyncClient() as c:
                r = await c.get(f"{API_BASE}/stats", headers=HEADERS, timeout=4)
                s = r.json()
            self.query_one("#sc", Static).update(
                f"[green]Online:[/green] {s.get('online',0)}/{s.get('total',0)}  "
                f"[red]Alerts:[/red] {s.get('active_alerts',0)}  "
                f"[yellow]Rooted:[/yellow] {s.get('rooted',0)}  "
                f"[cyan]Avg Risk:[/cyan] {s.get('avg_risk',0):.1f}/10")
        except:
            self.query_one("#sc",Static).update("[yellow]Server offline — run: python3 -m server.main[/yellow]")

class AIChatPanel(Static):
    def compose(self) -> ComposeResult:
        yield Label("🤖 AI Natural Language Commander", id="ai-title")
        yield ScrollableContainer(RichLog(id="ai-log", highlight=True, markup=True))
        yield Input(placeholder="e.g. 'Lock all rooted devices' | 'Disable WiFi on Device-003'", id="ai-input")

    def on_mount(self):
        log = self.query_one("#ai-log", RichLog)
        log.write("[cyan]AI MDM Assistant ready.[/cyan]")
        log.write("[dim]Type commands in plain English. Press Enter to send.[/dim]")

    async def on_input_submitted(self, event: Input.Submitted):
        nl = event.value.strip()
        if not nl: return
        log = self.query_one("#ai-log", RichLog)
        log.write(f"\n[bold cyan]You:[/bold cyan] {nl}")
        log.write("[dim]🤖 Thinking...[/dim]")
        event.input.value = ""
        try:
            async with httpx.AsyncClient(timeout=30) as c:
                r = await c.post(f"{API_BASE}/ai/command",
                                 json={"input":nl,"devices":"all"}, headers=HEADERS)
                result = r.json()
            cmd   = result.get("command","unknown")
            risk  = result.get("risk_level","LOW")
            expl  = result.get("explanation","")
            rc    = {"LOW":"green","MEDIUM":"yellow","HIGH":"red","CRITICAL":"bold red"}.get(risk,"white")
            log.write(f"[bold green]AI:[/bold green] `{cmd}` [{rc}]{risk}[/{rc}] — {expl}")
            if result.get("confirmation_required"):
                log.write("[yellow]⚠️ HIGH RISK — requires manual confirmation[/yellow]")
            else:
                log.write("[green]✅ Queued for execution[/green]")
        except Exception as e:
            log.write(f"[red]Error: {e}[/red]")

class MDMDashboard(App):
    CSS = """
    Screen { background: $background; }
    StatsPanel { height:5; border: solid $primary; padding:1 2; }
    DeviceTable { height:40%; border: solid $primary; }
    AlertPanel  { height:25%; border: solid $warning; }
    AIChatPanel { height:30%; border: solid $accent; padding:1; }
    """
    BINDINGS = [Binding("q","quit","Quit"), Binding("r","refresh","Refresh")]
    TITLE    = "🛡️ MDM Command Center"
    SUB_TITLE= "AI-Powered Fleet Security"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static(BANNER)
        yield StatsPanel()
        yield Horizontal(
            Vertical(Label("📱 Fleet Devices"), DeviceTable(),
                     Label("🚨 Live Alerts"),  AlertPanel()),
            Vertical(AIChatPanel()))
        yield Footer()

if __name__ == "__main__":
    MDMDashboard().run()
