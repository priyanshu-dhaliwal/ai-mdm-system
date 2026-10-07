import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from collections import defaultdict
from datetime import datetime
from ai.llm_engine import LLMEngine

llm = LLMEngine()

class AnomalyDetector:
    def __init__(self):
        self.models  = {}
        self.scalers = {}
        self.history = defaultdict(list)
        self.min_samples = 20

    def record_metrics(self, device_id: str, metrics: dict):
        features = [metrics.get("battery",0), metrics.get("cpu_usage",0),
                    metrics.get("ram_usage",0), metrics.get("network_rx",0),
                    metrics.get("network_tx",0), metrics.get("app_count",0),
                    1 if metrics.get("is_rooted") else 0]
        self.history[device_id].append(features)
        if len(self.history[device_id]) >= self.min_samples and \
           len(self.history[device_id]) % 10 == 0:
            self._train_model(device_id)

    def _train_model(self, device_id: str):
        X = np.array(self.history[device_id])
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        model = IsolationForest(contamination=0.05, random_state=42, n_estimators=100)
        model.fit(X_scaled)
        self.models[device_id]  = model
        self.scalers[device_id] = scaler

    def detect(self, device_id: str, metrics: dict) -> dict:
        self.record_metrics(device_id, metrics)
        if device_id not in self.models:
            return {"anomaly": False, "reason": "Building baseline..."}
        features = np.array([[metrics.get("battery",0), metrics.get("cpu_usage",0),
                               metrics.get("ram_usage",0), metrics.get("network_rx",0),
                               metrics.get("network_tx",0), metrics.get("app_count",0),
                               1 if metrics.get("is_rooted") else 0]])
        X_scaled   = self.scalers[device_id].transform(features)
        prediction = self.models[device_id].predict(X_scaled)[0]
        score      = self.models[device_id].score_samples(X_scaled)[0]
        is_anomaly = prediction == -1
        result     = {"anomaly": is_anomaly, "anomaly_score": float(score),
                      "timestamp": datetime.utcnow().isoformat()}
        if is_anomaly:
            result["ai_explanation"] = self._explain(device_id, metrics, score)
        return result

    def _explain(self, device_id: str, metrics: dict, score: float) -> str:
        history = np.array(self.history[device_id][-50:])
        avg = history.mean(axis=0).tolist()
        prompt = f"""Device {device_id} triggered anomaly (score: {score:.4f}).
Current: battery={metrics.get('battery')}% (avg {avg[0]:.1f}), cpu={metrics.get('cpu_usage')}% (avg {avg[1]:.1f}),
ram={metrics.get('ram_usage')}% (avg {avg[2]:.1f}), net_tx={metrics.get('network_tx')} MB (avg {avg[4]:.1f}),
rooted={metrics.get('is_rooted')}.
In 2 sentences: what does this anomaly indicate and what action should the admin take?"""
        return llm.query_sync(prompt)
