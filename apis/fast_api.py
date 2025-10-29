from fastapi import Depends, Header, FastAPI, HTTPException
import sqlite3, datetime

app = FastAPI()

# Edit to match actual database schema and logic (Including num interations, token expiry, etc.)
def verify_token(x_authorization: str = Header(None)) -> int:
    if not x_authorization:
        raise HTTPException(status_code=403, detail="Missing X-Authorization header")

    con = sqlite3.connect("registry.db")
    cur = con.cursor()
    cur.execute("SELECT user_id, expires_at FROM auth_tokens WHERE token = ?", (x_authorization,))
    row = cur.fetchone()
    con.close()

    if not row:
        raise HTTPException(status_code=403, detail="Invalid token")

    user_id, expires_at = row
    if expires_at and datetime.datetime.fromisoformat(expires_at) < datetime.datetime.utcnow():
        raise HTTPException(status_code=403, detail="Token expired")

    return user_id


@app.get("/")
async def read_root(user_auth: int = Depends(verify_token)):
    return {"message": "Welcome to the ModelReuseCLI API"}

@app.get("/health")
async def read_health():
    return {"status": "healthy"}

@app.get("/health/components")
async def read_health_components(user_auth: int = Depends(verify_token)):
    return {"components": ["component1", "component2"]}

@app.post("/artifacts")
async def create_artifact(artifact: dict, user_auth: int = Depends(verify_token)):
    return {"artifact": artifact}

@app.delete("/reset")
async def delete_artifacts(user_auth: int = Depends(verify_token)):
    return {"message": "All artifacts have been deleted"}

@app.get("/artifacts/{artifact_type}/{id}")
async def read_artifact(artifact_type: str, id: str, user_auth: int = Depends(verify_token)):
    return {"artifact_type": artifact_type, "id": id}

@app.put("/artifacts/{artifact_type}/{id}")
async def update_artifact(artifact_type: str, id: str, artifact: dict, user_auth: int = Depends(verify_token)):
    return {"artifact_type": artifact_type, "id": id, "updated_artifact": artifact}

@app.delete("/artifacts/{artifact_type}/{id}")
async def delete_artifact(artifact_type: str, id: str, user_auth: int = Depends(verify_token)):
    return {"message": f"Artifact {id} of type {artifact_type} has been deleted"}

@app.post("/artifact/{artifact_type}")
async def register_artifact(artifact_type: str, artifact: dict, user_auth: int = Depends(verify_token)):
    return {"artifact_type": artifact_type, "artifact": artifact}

@app.get("/artifact/model/{id}/rate")
async def rate_model(id: str, rating: int, user_auth: int = Depends(verify_token)):
    return {"model_id": id, "rating": rating}

@app.get("/artifact/{artifact_type}/{id}/cost")
async def get_artifact_cost(artifact_type: str, id: str, user_auth: int = Depends(verify_token)):
    return {"artifact_type": artifact_type, "id": id, "cost": 100}

# Add database creation (Logan started on it)
@app.put("/authenticate")
async def authenticate_user(credentials: dict):
    return {"authenticated": True}

@app.get("/artifact/byName/{name}")
async def get_artifact_by_name(name: str, user_auth: int = Depends(verify_token)):
    return {"name": name}

@app.get("/artifact/{artifact_type}/{id}/audit")
async def get_artifact_audit(artifact_type: str, id: str, user_auth: int = Depends(verify_token)):
    return {"artifact_type": artifact_type, "id": id, "audit": "audit_info"}

@app.get("/artifact/model/{id}/lineage")
async def get_artifact_lineage(id: str, user_auth: int = Depends(verify_token)):
    return {"model_id": id, "lineage": ["layer1", "layer2"]}

@app.post("/artifact/model/{id}/license-check")
async def check_model_license(id: str, license_info: dict, user_auth: int = Depends(verify_token)):
    return {"model_id": id, "license_info": license_info}

@app.post("/artifact/byRegEx")
async def get_artifact_by_regex(pattern: str, user_auth: int = Depends(verify_token)):
    return {"pattern": pattern, "artifacts": ["artifact1", "artifact2"]}

@app.get("/tracks")
async def get_tracks(user_auth: int = Depends(verify_token)):
    return {"tracks": ["track1", "track2"]}