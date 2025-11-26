# main.py
import os
from datetime import datetime

from fastapi import FastAPI
from pydantic import BaseModel
from cassandra.cluster import Cluster
from cassandra.policies import DCAwareRoundRobinPolicy

# Leer variables de entorno
CONTACT_POINTS = os.getenv("CASSANDRA_CONTACT_POINTS", "").split(",")
DATACENTER = os.getenv("CASSANDRA_DATACENTER", "datacenter1")
KEYSPACE = os.getenv("CASSANDRA_KEYSPACE", "iot")

app = FastAPI(title="IoT Readings API - Cassandra Distributed (Cloud Run)")

cluster = None
session = None


class ReadingIn(BaseModel):
    sede: str
    sensor_type: str
    sensor_id: str
    value: float


@app.on_event("startup")
def startup():
    global cluster, session

    if not CONTACT_POINTS or CONTACT_POINTS == [""]:
        raise RuntimeError("CASSANDRA_CONTACT_POINTS no está configurado")

    cluster = Cluster(
        CONTACT_POINTS,
        load_balancing_policy=DCAwareRoundRobinPolicy(local_dc=DATACENTER),
        port=9042,  # muy importante
    )
    session = cluster.connect(KEYSPACE)


@app.on_event("shutdown")
def shutdown():
    global cluster
    if cluster:
        cluster.shutdown()


@app.get("/")
def root():
    return {"status": "ok", "message": "IoT API running on Cloud Run"}


@app.post("/readings")
def create_reading(reading: ReadingIn):
    ts = datetime.utcnow()
    query = """
        INSERT INTO readings (sede, sensor_type, sensor_id, ts, value)
        VALUES (%s, %s, %s, %s, %s)
    """
    session.execute(
        query,
        (reading.sede, reading.sensor_type, reading.sensor_id, ts, reading.value),
    )
    return {"status": "ok", "timestamp": ts.isoformat()}


@app.get("/readings")
def list_readings(sede: str, sensor_type: str, limit: int = 20):
    query = """
        SELECT sede, sensor_type, sensor_id, ts, value
        FROM readings
        WHERE sede = %s AND sensor_type = %s
        LIMIT %s
    """
    rows = session.execute(query, (sede, sensor_type, limit))
    return [
        {
            "sede": r.sede,
            "sensor_type": r.sensor_type,
            "sensor_id": r.sensor_id,
            "ts": r.ts.isoformat(),
            "value": r.value,
        }
        for r in rows
    ]
