from sqlalchemy import create_engine, Column, String, Integer, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import uuid

DATABASE_URL = "sqlite:///./data/mdm.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Device(Base):
    __tablename__ = "devices"
    id             = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name           = Column(String, nullable=False)
    android_id     = Column(String, unique=True)
    ip_address     = Column(String)
    os_version     = Column(String)
    battery        = Column(Integer, default=0)
    storage_used   = Column(Float, default=0)
    storage_total  = Column(Float, default=0)
    wifi_ssid      = Column(String)
    is_online      = Column(Boolean, default=False)
    is_rooted      = Column(Boolean, default=False)
    policy_group   = Column(String, default="default")
    last_seen      = Column(DateTime, default=datetime.utcnow)
    enrolled_at    = Column(DateTime, default=datetime.utcnow)
    location       = Column(JSON, default=dict)
    installed_apps = Column(JSON, default=list)
    risk_score     = Column(Float, default=0.0)

class Alert(Base):
    __tablename__ = "alerts"
    id           = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id    = Column(String)
    device_name  = Column(String)
    severity     = Column(String)
    category     = Column(String)
    title        = Column(String)
    description  = Column(Text)
    ai_analysis  = Column(Text)
    resolved     = Column(Boolean, default=False)
    created_at   = Column(DateTime, default=datetime.utcnow)

class PolicyRule(Base):
    __tablename__ = "policies"
    id           = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name         = Column(String)
    group        = Column(String, default="default")
    rule_type    = Column(String)
    condition    = Column(JSON)
    action       = Column(JSON)
    ai_generated = Column(Boolean, default=False)
    active       = Column(Boolean, default=True)

class CommandLog(Base):
    __tablename__ = "command_logs"
    id           = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id    = Column(String)
    command      = Column(String)
    source       = Column(String)
    result       = Column(Text)
    executed_at  = Column(DateTime, default=datetime.utcnow)

class DeviceMetrics(Base):
    __tablename__ = "device_metrics"
    id           = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id    = Column(String)
    timestamp    = Column(DateTime, default=datetime.utcnow)
    battery      = Column(Integer)
    cpu_usage    = Column(Float)
    ram_usage    = Column(Float)
    network_rx   = Column(Float)
    network_tx   = Column(Float)

def init_db():
    import os
    os.makedirs("data", exist_ok=True)
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized at data/mdm.db")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
