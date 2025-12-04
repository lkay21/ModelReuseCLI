from urllib import response

import json
from fastapi import Depends, Header, FastAPI, HTTPException, Body, Query
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
from model import Code, Dataset, Model
import logging
import requests
import re

PURDUE_GENAI_API_KEY = os.getenv("GEN_AI_STUDIO_API_KEY")
PURDUE_GENAI_URL = "https://genai.rcac.purdue.edu/api/chat/completions"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("api")

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
database_dir = "./databases/database.db"

AWS_REGION = os.getenv("AWS_REGION", "us-east-2")
MODEL_TABLE_NAME = os.getenv("MODEL_TABLE_NAME", "models")  # default to "models"

api_key = os.getenv("GEN_AI_STUDIO_API_KEY")
if api_key:
    logger.info(f"API key loaded successfully {api_key[:4]}****")
else:
    logger.warning("API key not found")

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



def _genai_single_url(dataset_bool: bool, code_bool: bool, url: str, model_url: str) -> Optional[str]:
    """
    Call Purdue GenAI Studio with a constrained prompt that should return a single number.
    Returns None on any error or if not configured. Satisfies the Phase-1 LLM usage.
    """
    context_prompt = f"context_prompt: Below you are given a TEST_URL. The TEST_URL will either point to a dataset or code repository. In the inputValuePromt, you will find this TEST_URL and will be told whether or not the TEST_URL is a dataset or code repository from boolean values. Once given this information your task is simple. Rate the likelihood that the given TEST_URL will match a model artifact in our system. To do so, your first priority will always be to extract information from a README file from the MODEL_URL, not the TEST_URL, if it exists. If no README file exists, you may try to match other relvant information of the TEST_URL to any of the input context you are given in the input_val_promt section of this promt.Your output should be a single rating 0.0 to 1.0, with 1.0 being a perfect match and 0.0 being no match at all.\n"
    input_val_promt = f"input_val_prompt: Here is the TEST_URL you will evaluate: {url}\nHere is whether or not the TEST_URL is a dataset: {dataset_bool}\nHere is whether or not the TEST_URL is code repository: {code_bool}\nHere is the MODEL_URL: {model_url}\n"
    prompt = context_prompt + input_val_promt

    if not PURDUE_GENAI_API_KEY:
        logger.info("GEN_AI_STUDIO_API_KEY not set; skipping GenAI enrichment.")
        return None
    try:
        headers = {
            "Authorization": f"Bearer {PURDUE_GENAI_API_KEY}",
            "Content-Type": "application/json",
        }
        body = {
            "model": "llama3.1:latest",
            "messages": [
                {"role": "system", "content": "Reply with exactly the rating you calculate from the successive prompts. Range 0.0 to 1.0."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0,
        }
        resp = requests.post(
            PURDUE_GENAI_URL, headers=headers, json=body, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        text: str = data["choices"][0]["message"]["content"].strip()
        m = re.search(r"https?://\S+", text)
        return m.group(0) if m else None
    except Exception as e:
        logger.warning(f"GenAI call failed: {e}")
        return None
    

def match_dataset_code_to_model(dataset_url: str = None, code_url: str = None):
    best_match_rating = 0.0
    best_model_id = None


    scan = model_table.scan()

    for item in scan['Items']:
        model_id = item.get("model_id")
        model_url = item.get("url")

        if dataset_url is not None:
            curr_rating = _genai_single_url(dataset_bool=True, code_bool=False, url=dataset_url, model_url=model_url)
        elif code_url is not None:
            curr_rating = _genai_single_url(dataset_bool=False, code_bool=True, url=code_url, model_url=model_url)
        else:
            return None
        
        if curr_rating is not None:
            try:
                curr_rating_float = float(curr_rating)
                if curr_rating_float > best_match_rating:
                    best_match_rating = curr_rating_float
                    best_model_id = model_id
            except ValueError:
                logger.warning(f"GenAI returned non-float rating: {curr_rating}")
                continue
            
    return best_model_id


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
    logger.info("GET / called x_authorization=%s", x_authorization)
    return {"message": "Welcome to the ModelReuseCLI API"}

@app.get("/health")
async def read_health():
    return {"status": "healthy"}

@app.get("/health/components")
async def read_health_components(x_authorization: str = Header(None, alias="X-Authorization")):
    return {"components": ["component1", "component2"]}

@app.post("/artifacts")
async def find_artifacts(x_authorization: str = Header(None), queries: List[ArtifactQuery] = Body(...), offset: int = Query(0)):
    logger.info(f"POST /artifacts called, x_authorization={x_authorization}, queries={queries}, offset={offset}")
    artifacts = []

    if not queries or any(not query.name for query in queries):
        raise HTTPException(status_code=400, detail="error in request body")


    for index, query in enumerate(queries):
        # first query is a star, indicating all artifacts
        name = query.name
        if(index == 0 and name == "*"):
            try:
                scan = model_table.scan()


                if len(query.types) != 0:
                    for item in scan['Items']:
                        if item.get("type") in query.types:
                            artifact = {
                                "name": item.get("name"),
                                "id": item.get("model_id"),
                                "type": item.get("type")
                            }

                            artifacts.append(artifact)
                else:
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
                        if len(query.types) == 0 or item.get("type") in query.types:
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
async def read_artifact(artifact_type: str, id: str, x_authorization: str = Header(None)):
    logger.info(f"GET /artifacts/{artifact_type}/{id} called, x_authorization={x_authorization}")

    # 1) Validate ID is an integer
    try:
        model_id = int(id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid artifact ID")

    try:
        # 2) Look up item by model_id
        query = model_table.get_item(Key={"model_id": model_id})
        item = query.get("Item")

        # 3) Not found → 404
        if not item:
            raise HTTPException(status_code=404, detail="Artifact DNE")

        # 4) Type mismatch → also 404 (ID exists but wrong artifact_type)
        if item.get("type") != artifact_type:
            raise HTTPException(status_code=404, detail="Artifact DNE")

        name = item.get("name")
        url = item.get("url")

        # 5) Response shape consistent with ingest_model
        return JSONResponse(
            status_code=200,
            content={
                "metadata": {
                    "name": name,
                    "id": model_id,
                    "type": artifact_type,
                },
                "data": {
                    "url": url,
                    "download_url": None,
                },
            },
        )

    except HTTPException:
        # Let explicit HTTPExceptions propagate unchanged
        raise
    except Exception as e:
        # Unexpected backend failures → 500
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve artifact: {e}",
        )

@app.put("/artifacts/{artifact_type}/{id}")
async def update_artifact(
    artifact_type: str,
    id: str,
    artifact: dict,
    x_authorization: str = Header(None, alias="X-Authorization"),
):
    """
    Update an existing artifact in the DynamoDB 'models' table.

    - `id` is the model_id (Number) in DynamoDB.
    - `artifact` is a JSON body with the fields you want to update,
      e.g. {"name": "new-name"} or {"url": "https://new-url"}.
    """

    # 1) Parse id -> int (since model_id is stored as a Number)
    try:
        model_id = int(id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid artifact ID")

    # 2) Make sure the item exists and the type matches
    try:
        resp = model_table.get_item(Key={"model_id": model_id})
        item = resp.get("Item")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read artifact: {e}")

    if not item:
        raise HTTPException(status_code=404, detail="Artifact DNE")

    if item.get("type") != artifact_type:
        # ID exists, but under a different type (e.g., dataset vs model)
        raise HTTPException(status_code=404, detail="Artifact DNE")

    # 3) Build the DynamoDB update expression
    # We'll update any fields provided in the body EXCEPT id/model_id
    if not artifact:
        raise HTTPException(status_code=400, detail="No fields provided to update")

    update_parts = []
    expr_attr_values = {}
    idx = 0

    for key, value in artifact.items():
        if key in ("id", "model_id"):  # don't let the client change the primary key
            continue

        placeholder = f":val{idx}"
        update_parts.append(f"{key} = {placeholder}")
        expr_attr_values[placeholder] = value
        idx += 1

    if not update_parts:
        raise HTTPException(status_code=400, detail="No valid fields provided to update")

    update_expression = "SET " + ", ".join(update_parts)

    # 4) Perform the update
    try:
        update_resp = model_table.update_item(
            Key={"model_id": model_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expr_attr_values,
            ReturnValues="ALL_NEW",  # return the updated item
        )
        updated_item = update_resp.get("Attributes", {})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update artifact: {e}")

    # 5) Return the updated artifact (simple shape)
    return {
        "name": updated_item.get("name"),
        "id": updated_item.get("model_id"),
        "type": updated_item.get("type"),
        "url": updated_item.get("url"),
        # include any extra fields you might have added
        "raw": updated_item,
    }

@app.delete("/artifacts/{artifact_type}/{id}")
async def delete_artifact(
    artifact_type: str,
    id: str,
    x_authorization: str = Header(None, alias="X-Authorization"),
):
    """
    Delete a single artifact whose partition key is model_id.

    - `id` is expected to be the DynamoDB model_id (Number).
    """

    # 1) Parse id into an int (model_id is stored as a Number)
    try:
        model_id = int(id)
    except ValueError:
        # Bad path param like "invalidId99999"
        raise HTTPException(status_code=400, detail="Invalid artifact ID")

    try:
        # 2) Check if the item exists
        resp = model_table.get_item(Key={"model_id": model_id})
        item = resp.get("Item")

        if not item:
            # Nothing with this model_id in the table
            raise HTTPException(status_code=404, detail="Artifact DNE")

        # 3) Ensure type matches the URL path (model/dataset/code)
        if item.get("type") != artifact_type:
            # ID exists but under a different type
            raise HTTPException(status_code=404, detail="Artifact DNE")

        # 4) Actually delete the item
        model_table.delete_item(Key={"model_id": model_id})

        # 5) Return a simple success message
        return {
            "message": f"Artifact {model_id} of type {artifact_type} has been deleted"
        }

    except HTTPException:
        # Re-raise our explicit HTTP errors unchanged
        raise
    except Exception as e:
        # Any unexpected DynamoDB / other failure
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete artifact: {e}",
        )


# @app.post("/artifact/{artifact_type}")
# async def register_artifact(artifact_type: str, artifact: dict, user_auth: int = Depends(verify_token)):
#     return {"artifact_type": artifact_type, "artifact": artifact}

@app.get("/artifact/model/{id}/rate")
async def rate_model(id: str, authorization: str = Header(None, alias="Authorization"), x_authorization: str = Header(None, alias="X-Authorization")):
    token_header = authorization or x_authorization
    logger.info(f"GET /artifact/model/{id}/rate called, x_authorization={token_header}")
    if not int(id):
        raise HTTPException(status_code=400, detail="Invalid artifact ID")
    
    try: 
        query = model_table.get_item(
            Key={'model_id': int(id)}
        )

        item = query.get('Item')
        if not item:
            raise HTTPException(status_code=404, detail="Artifact DNE")

        url = item.get("url")

        model_obj = Model(url=url, id=id)
        rating = model_obj.evaluate()

        return rating

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"The artifact rating system encountered an error while computing at least one metric.")

# @app.get("/artifact/model/{id}/rate")
# async def rate_model(id: str, rating: int, user_auth: int = Depends(verify_token)):
#     return {"model_id": id, "rating": rating}

@app.get("/artifact/{artifact_type}/{id}/cost")
async def get_artifact_cost(artifact_type: str, id: str, x_authorization: str = Header(None, alias="X-Authorization")):
    return {"artifact_type": artifact_type, "id": id, "cost": 100}

@app.post("/artifact/{artifact_type}")
async def ingest_model(artifact_type: str, payload: ModelIngestRequest):
    logger.info(f"POST /artifact/{artifact_type} ingest called with payload={payload.dict()}")
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
    logger.info(f"Extracted name '{name}' from URL '{payload.url}'")

    # Need to add naming logic call form phase 1
    item = {
        "model_id": unique_id,    # DynamoDB partition key
        "url": payload.url,
        "type": artifact_type,
        "name": name
    }

    try:
        model_table.put_item(Item=item)

        if artifact_type == "dataset" or artifact_type == "code":
            matched_model_id = match_dataset_code_to_model(
                dataset_url=payload.url if artifact_type == "dataset" else None,
                code_url=payload.url if artifact_type == "code" else None
            )
            if matched_model_id is not None:
                logger.info(f"Dataset/Code URL '{payload.url}' matched to model_id {matched_model_id}")
            else:
                logger.info(f"Dataset/Code URL '{payload.url}' did not match any existing model")

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

from typing import Optional

@app.get("/artifact/byName/{name}")
async def get_artifact_by_name(
    name: str,
    artifact_type: Optional[str] = Query(None, alias="type"),
    x_authorization: str = Header(None),
):
    """
    Look up artifacts by name, optionally filtered by type via ?type=model|dataset|code.

    Returns:
      
200 + list of matching artifacts when matches exist
404 when no artifacts match the given name (and type, if provided)"""
    try:
        scan = model_table.scan()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve artifacts: {e}",)

    artifacts = []

    for item in scan.get("Items", []):
        item_name = item.get("name")
        item_type = item.get("type")

        if item_name != name:
            continue

        # If caller specified a type, enforce it
        if artifact_type is not None and item_type != artifact_type:
            continue

        artifacts.append(
            {
                "name": item_name,
                "id": item.get("model_id"),
                "type": item_type,
            }
        )

    if not artifacts:
        # Name (or name+type) not found
        raise HTTPException(status_code=404, detail="Artifact DNE")

    return artifacts

@app.get("/artifact/{artifact_type}/{id}/audit")
async def get_artifact_audit(artifact_type: str, id: str, x_authorization: str = Header(None, alias="X-Authorization")):
    return {"artifact_type": artifact_type, "id": id, "audit": "audit_info"}

@app.get("/artifact/model/{id}/lineage")
async def get_artifact_lineage(id: str, x_authorization: str = Header(None, alias="X-Authorization")):
    return {"model_id": id, "lineage": ["layer1", "layer2"]}

@app.post("/artifact/model/{id}/license-check")
async def check_model_license(id: str, license_info: dict, x_authorization: str = Header(None, alias="X-Authorization")):
    return {"model_id": id, "license_info": license_info}

@app.post("/artifact/byRegEx")
async def get_artifact_by_regex(pattern: str, x_authorization: str = Header(None, alias="X-Authorization")):
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