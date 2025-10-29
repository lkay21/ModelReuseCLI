import string
from fastapi import FastAPI
import sqlite3
import secrets
import jwt
import math as m
import string

database_dir = "./database.db"

def create_authentication_token(user_id, database_dir=database_dir):

    secret_key = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(64))

    now = m.floor(m.time() / 1000) 
    expiration = now + (10 * 60 * 60)

    jwt_header = {
        "alg": "HS256",
        "typ": "JWT"
    }

    jwt_payload = {
        "iat": now,
        "exp": expiration,
        "sub": user_id,
        "role": "admin"
    }

    token = jwt.encode(jwt_payload, secret_key, algorithm="HS256", headers=jwt_header)

    conn = sqlite3.connect(database_dir)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET secret_key = ? WHERE id = ?", (token, user_id))
    conn.commit()
    conn.close()

def create_users_table():
    conn = sqlite3.connect(database_dir)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            secret_key TEXT NOT NULL,
            num_interactions INTEGER DEFAULT 0,
            api_time DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def generate_user_secret_key():
    key = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(64))
    return key



app = FastAPI()

@app.get("/")
async def read_root():
    return {"message": "Welcome to the ModelReuseCLI API"}

@app.get("/health")
async def read_health():
    return {"status": "healthy"}

@app.get("/health/components")
async def read_health_components():
    return {"components": ["component1", "component2"]}

@app.post("/artifacts")
async def create_artifact(artifact: dict):
    return {"artifact": artifact}

@app.delete("/reset")
async def delete_artifacts():
    return {"message": "All artifacts have been deleted"}

@app.get("/artifacts/{artifact_type}/{id}")
async def read_artifact(artifact_type: str, id: str):
    return {"artifact_type": artifact_type, "id": id}

@app.put("/artifacts/{artifact_type}/{id}")
async def update_artifact(artifact_type: str, id: str, artifact: dict):
    return {"artifact_type": artifact_type, "id": id, "updated_artifact": artifact}

@app.delete("/artifacts/{artifact_type}/{id}")
async def delete_artifact(artifact_type: str, id: str):
    return {"message": f"Artifact {id} of type {artifact_type} has been deleted"}

@app.post("/artifact/{artifact_type}")
async def register_artifact(artifact_type: str, artifact: dict):
    return {"artifact_type": artifact_type, "artifact": artifact}

@app.get("/artifact/model/{id}/rate")
async def rate_model(id: str, rating: int):
    return {"model_id": id, "rating": rating}

@app.get("/artifact/{artifact_type}/{id}/cost")
async def get_artifact_cost(artifact_type: str, id: str):
    return {"artifact_type": artifact_type, "id": id, "cost": 100}

@app.put("/authenticate")
async def authenticate_user(credentials: dict):
    return {"authenticated": True}

@app.get("/artifact/byName/{name}")
async def get_artifact_by_name(name: str):
    return {"name": name}

@app.get("/artifact/{artifact_type}/{id}/audit")
async def get_artifact_audit(artifact_type: str, id: str):
    return {"artifact_type": artifact_type, "id": id, "audit": "audit_info"}

@app.get("/artifact/model/{id}/lineage")
async def get_artifact_lineage(id: str):
    return {"model_id": id, "lineage": ["layer1", "layer2"]}

@app.post("/artifact/model/{id}/license-check")
async def check_model_license(id: str, license_info: dict):
    return {"model_id": id, "license_info": license_info}

@app.post("/artifact/byRegEx")
async def get_artifact_by_regex(pattern: str):
    return {"pattern": pattern, "artifacts": ["artifact1", "artifact2"]}

@app.get("/tracks")
async def get_tracks():
    return {"tracks": ["track1", "track2"]}