from fastapi import Depends, Header, FastAPI, HTTPException, Body
from fastapi.responses import JSONResponse
from utils.url_parser import extract_name_from_url
import string
import sqlite3
import secrets
import jwt
import math as m
import string
import time
import bcrypt
import os
from dotenv import load_dotenv
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
import boto3
from boto3.dynamodb.conditions import Key


load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
database_dir = "./databases/database.db"

AWS_REGION = os.getenv("AWS_REGION", "us-east-2")
MODEL_TABLE_NAME = os.getenv("MODEL_TABLE_NAME", "models")  # default to "models"

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
model_table = dynamodb.Table(MODEL_TABLE_NAME)  # this will point to the "models" table

last_time = 0   

class ModelArtifact(BaseModel):
    id: str                      # will map to "model_id" in DynamoDB
    name: str
    provider: str = "custom"     # e.g. "huggingface"
    task: Optional[str] = None
    metadata: Dict[str, Any] = {}
    tags: List[str] = []

class ModelIngestRequest(BaseModel):
    url: str

class ArtifactQuery(BaseModel):
    name: str
    id: Optional[str] = None
    types: Optional[List[str]] = None


def create_authentication_token(user_id, database_dir=database_dir):
    now = m.floor(time.time() / 1000) 
    expiration = now + (10 * 60 * 60)

    jwt_payload = {
        "iat": now,
        "exp": expiration,
        "sub": user_id,
        "role": "admin"
    }

    token = jwt.encode(jwt_payload, SECRET_KEY, algorithm="HS256")

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
            password TEXT NOT NULL,
            secret_key TEXT NOT NULL,
            num_interactions INTEGER DEFAULT 0,
            api_time DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def token_from_secret_key(secret_key):
    try:
        payload = jwt.decode(secret_key, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:   
        return None

def add_user(username, password, secret_key):
    password = hash_password(password)
    conn = sqlite3.connect(database_dir)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, password, secret_key) VALUES (?, ?, ?)", (username, password, secret_key))
    conn.commit()
    conn.close()
    
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def check_password(password: str, hashed_password: str):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

app = FastAPI()

# Edit to match actual database schema and logic (Including num interations, token expiry, etc.)
def verify_token(x_authorization: str = Header(None)) -> int:
    if not x_authorization:
        raise HTTPException(status_code=403, detail="Missing X-Authorization header")

    con = sqlite3.connect(database_dir)
    cur = con.cursor()
    cur.execute("SELECT id, secret_key, num_interactions, api_time FROM users WHERE secret_key = ?", (x_authorization,))
    row = cur.fetchone()
    con.close()

    if not row:
        raise HTTPException(status_code=403, detail="Invalid token")

    id, secret_key, num_interactions, api_time = row
    if api_time - time.time() > 60000 or num_interactions > 1000:
        raise HTTPException(status_code=403, detail="Token expired")
    else:
        num_interactions += 1
        con = sqlite3.connect(database_dir)
        cur = con.cursor()
        cur.execute("UPDATE users SET num_interactions = ? WHERE id = ?", (num_interactions, id))
        con.commit()
        con.close()

    return id


@app.get("/")
async def read_root(x_authorization: str = Header(None)):
    return {"message": "Welcome to the ModelReuseCLI API"}

@app.get("/health")
async def read_health():
    return {"status": "healthy"}

@app.get("/health/components")
async def read_health_components(user_auth: int = Depends(verify_token)):
    return {"components": ["component1", "component2"]}

@app.post("/artifacts")
async def find_artifacts(x_authorization: str = Header(None), queries: List[ArtifactQuery] = Body(...)):
    artifacts = []

    if not queries or any(not query.name for query in queries):
        raise HTTPException(status_code=400, detail="error in request body")


    for index, query in enumerate(queries):
        # first query is a star, indicating all artifacts
        name = query.name
        id = query.id
        if(index == 0 and name == "*"):
            try:
                scan = model_table.scan()

                for item in scan['Items']:

                    artifact = {
                        "name": item.get("name"),
                        "id": item.get("model_id"),
                        "type": item.get("type")
                    }

                    artifacts.append(artifact)
                
                break
            except Exception as e:
                raise HTTPException(status_code=403, detail=f"Failed to retrieve artifacts: {e}")
        else:     
            try: 
                scan = model_table.scan()

                for item in scan['Items']:
                    matched = False

                    if query.id is not None and item.get("model_id") == query.id:
                        matched = True
                    elif item.get("name") == query.name:
                        if query.types is None or item.get("type") in query.types:
                            matched = True

                    if matched:
                        artifacts.append({
                            "name": item.get("name"),
                            "id": item.get("model_id"),
                            "type": item.get("type")
                        })


            except Exception as e:
                raise HTTPException(status_code=403, detail=f"Failed to retrieve artifacts: {e}")
    
    return artifacts

@app.delete("/reset")
async def delete_artifacts(x_authorization: str = Header(None)):
    try:
        scan = model_table.scan()
        with model_table.batch_writer() as batch:
            for each in scan['Items']:
                batch.delete_item(
                    Key={
                        'model_id': each['model_id']
                    }
                )

        

    # 401 for no permission, 403 for failed auth
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Failed to delete artifacts: {e}")
    
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

# @app.post("/artifact/{artifact_type}")
# async def register_artifact(artifact_type: str, artifact: dict, user_auth: int = Depends(verify_token)):
#     return {"artifact_type": artifact_type, "artifact": artifact}

@app.post("/artifact/model/{id}/rate")
async def rate_model(id: str, rating: int, user_auth: int = Depends(verify_token)):
    if rating < 1 or rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    try:
        model_table.update_item(
            Key={"model_id": id},  # uses the partition key
            UpdateExpression="SET rating = :r, rated_at = :t, rated_by_user_id = :u",
            ExpressionAttributeValues={
                ":r": rating,
                ":t": int(time.time()),
                ":u": user_auth,
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update rating: {e}")

    return {"model_id": id, "rating": rating}

# @app.get("/artifact/model/{id}/rate")
# async def rate_model(id: str, rating: int, user_auth: int = Depends(verify_token)):
#     return {"model_id": id, "rating": rating}

@app.get("/artifact/{artifact_type}/{id}/cost")
async def get_artifact_cost(artifact_type: str, id: str, user_auth: int = Depends(verify_token)):
    return {"artifact_type": artifact_type, "id": id, "cost": 100}

@app.post("/artifact/{artifact_type}")
async def ingest_model(artifact_type: str, payload: ModelIngestRequest):
    global last_time
    """
    Renegotiated ingest: register a *model* artifact.

    - Path must be /artifact/model
    - Body: {"model_id": "...", "url": "..."}
    - Saves only model_id + url into DynamoDB 'models' table.
    """
    # Only support model artifacts here
    supported_types = ["model", "dataset", "code"]
    if artifact_type not in supported_types:
        raise HTTPException(
            status_code=400,
            detail="Only artifact_types 'model', 'dataset', and 'code' are supported for ingestion.",
        )

    if not payload.url:
        # Match the 400 description text from the spec
        raise HTTPException(
            status_code=400,
            detail="There is missing field(s) in the artifact_query or it is formed improperly, or is invalid.",
        )

    unique_id = int(time.time() * 1000);
    if( unique_id == last_time ):
        unique_id += 1
    last_time = unique_id    

    name = extract_name_from_url(payload.url)[1]

    # Need to add naming logic call form phase 1
    item = {
        "model_id": unique_id,    # DynamoDB partition key
        "url": payload.url,
        "type": artifact_type,
        "name": name
    }

    try:
        model_table.put_item(Item=item)

        response = JSONResponse(
            status_code=201, 
            content={
                "metadata": {
                    "name": name, 
                    "id": unique_id, 
                    "type": artifact_type
                },
                "data": {
                    "url": payload.url,
                    "download_url": None
                }
            }
        )

        return response
    
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to store model artifact.",
        )
    


    # Shape the response like an artifact summary:
    return


# Add database creation (Logan started on it)
@app.put("/authenticate")
async def authenticate_user(credentials: dict):

    if "user" not in credentials or ("name" not in credentials["user"] or "is_admin" not in credentials["user"]):
        raise HTTPException(status_code=400, detail="Invalid credentials format")
    elif "secret" not in credentials or "password" not in credentials["secret"]:
        raise HTTPException(status_code=400, detail="Invalid credentials format")
    
    # Gather User Credentials via Input JSON
    username = credentials["user"]["name"]
    is_admin = credentials["user"]["is_admin"]
    password = credentials["secret"]["password"]

    conn = sqlite3.connect(database_dir)
    cursor = conn.cursor()
    cursor.execute("SELECT id, password, secret_key FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()

    # If User Exists, Check Password Generate Token
    if row:
        user_id, stored_hashed_password, stored_token = row
        if not check_password(password, stored_hashed_password):
            raise HTTPException(status_code=401, detail="The user or password is invalid.")
        else:
            create_authentication_token(user_id)
            cursor.execute("SELECT secret_key FROM users WHERE id = ?", (user_id,))
            stored_token = token_from_secret_key(cursor.fetchone()[0])
            conn.close()
            return f"\"\\\"bearer {stored_token}\\\"\""
    # If User Does Not Exist, Create User and Generate Token
    else:
        add_user(username, password, "")
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        user_id = cursor.fetchone()[0]
        create_authentication_token(user_id)
        cursor.execute("SELECT secret_key FROM users WHERE id = ?", (user_id,))
        stored_token = token_from_secret_key(cursor.fetchone()[0])
        conn.close()
        return f"\"\\\"bearer {stored_token}\\\"\""

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
async def get_tracks():
    return {"plannedTracks": ["Access control track"]}

@app.on_event("startup")
def startup_event():
    # Ensure the database directory exists
    db_dir = os.path.dirname(database_dir)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)

    # Initialize the database and create the users table
    create_users_table()
