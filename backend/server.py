from fastapi import FastAPI, APIRouter, HTTPException, Body
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone

# Load env
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection - MUST use envs only
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url, uuidRepresentation="standard")
db = client[os.environ['DB_NAME']]

# FastAPI app + router with /api prefix
app = FastAPI()
api_router = APIRouter(prefix="/api")

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper: time + mongo serialization

def now_iso():
    return datetime.now(timezone.utc).isoformat()

# Data Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: str = Field(default_factory=now_iso)

class StatusCheckCreate(BaseModel):
    client_name: str

# Initial Placer models
income_brackets_default = [
    "< $25k", "$25k - $50k", "$50k - $100k", "$100k - $200k", ">$200k"
]

education_levels_default = [
    "High School", "Some College", "Associate", "Bachelor's", "Master's", "PhD"
]

ethnicity_options_default = [
    "Asian", "Black", "Hispanic/Latino", "Middle Eastern", "Native American", "White", "Mixed", "Other"
]

class UserProfileCreate(BaseModel):
    first_name: str
    other_given_names: Optional[str] = None
    last_name: str
    email: EmailStr
    phone_number: Optional[str] = None
    education: Optional[str] = None
    where_you_live: Optional[str] = None
    age: Optional[int] = None
    income_bracket: Optional[str] = None
    interests: List[str] = Field(default_factory=list, description="List 3 in order of importance")
    ethnicity: Optional[str] = None

class UserProfile(BaseModel):
    id: str
    created_at: str
    updated_at: str
    # Same fields as create
    first_name: str
    other_given_names: Optional[str] = None
    last_name: str
    email: EmailStr
    phone_number: Optional[str] = None
    education: Optional[str] = None
    where_you_live: Optional[str] = None
    age: Optional[int] = None
    income_bracket: Optional[str] = None
    interests: List[str] = []
    ethnicity: Optional[str] = None

class ExperienceCard(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    rationale: Optional[str] = None
    confidence: float = 0.6

class SwipeRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    card_id: str
    direction: str  # right/left/up/down
    created_at: str = Field(default_factory=now_iso)

# Basic routes
@api_router.get("/")
async def root():
    return {"message": "Hello World"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_obj = StatusCheck(**input.dict())
    await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**sc) for sc in status_checks]

# ---------- Initial Placer API ----------
# OpenAI integration (user-provided key)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

def ensure_openai_ready():
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OpenAI key not configured. Add OPENAI_API_KEY in backend/.env and restart backend")

# Signup
@api_router.post("/placer/signup", response_model=UserProfile)
async def placer_signup(payload: UserProfileCreate):
    # minimal validation: interests up to 3
    interests = (payload.interests or [])[:3]

    profile_doc = {
        "_id": str(uuid.uuid4()),
        "created_at": now_iso(),
        "updated_at": now_iso(),
        **payload.dict(),
        "interests": interests,
    }
    await db.users.insert_one(profile_doc)
    return UserProfile(
        id=profile_doc["_id"],
        created_at=profile_doc["created_at"],
        updated_at=profile_doc["updated_at"],
        first_name=profile_doc["first_name"],
        other_given_names=profile_doc.get("other_given_names"),
        last_name=profile_doc["last_name"],
        email=profile_doc["email"],
        phone_number=profile_doc.get("phone_number"),
        education=profile_doc.get("education"),
        where_you_live=profile_doc.get("where_you_live"),
        age=profile_doc.get("age"),
        income_bracket=profile_doc.get("income_bracket"),
        interests=profile_doc.get("interests", []),
        ethnicity=profile_doc.get("ethnicity"),
    )

# Generate initial experience cards via OpenAI from profile
class SuggestInput(BaseModel):
    user_id: str
    count: int = 8

@api_router.post("/placer/suggest", response_model=List[ExperienceCard])
async def placer_suggest(body: SuggestInput):
    ensure_openai_ready()
    from openai import OpenAI
    user = await db.users.find_one({"_id": body.user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Collect existing titles to avoid duplicates
    existing_docs = await db.experience_cards.find({"user_id": body.user_id}).to_list(1000)
    existing_titles = { (d.get("title") or "").strip().lower() for d in existing_docs }

    try:
        system = (
            "You generate life experience cards based on a user's basic profile. "
            "Return STRICT valid JSON array of objects with keys: title, description, rationale, confidence (0-1). "
            "Experiences should be realistic day-to-day, education/career, social, and hobbies. "
            "Keep titles short, descriptions concrete."
        )
        user_msg = {
            "first_name": user.get("first_name"),
            "education": user.get("education"),
            "location": user.get("where_you_live"),
            "age": user.get("age"),
            "income_bracket": user.get("income_bracket"),
            "interests": user.get("interests", []),
            "ethnicity": user.get("ethnicity"),
            "count": body.count,
            "avoid_titles": list(existing_titles),
        }
        client = OpenAI(api_key=OPENAI_API_KEY)
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"Profile JSON:\n{user_msg}\nReturn JSON array only. Avoid rephrasing or repeating any items whose lowercased titles appear in avoid_titles."},
            ],
            response_format={"type": "json_object"},
            temperature=0.4,
            max_tokens=800,
        )
        content = resp.choices[0].message.content
        import json
        data = json.loads(content)
        items = data.get("items") if isinstance(data, dict) else data
        if items is None and isinstance(data, dict):
            items = data.get("experiences")
        if items is None:
            raise ValueError("Model did not return items array")
        cards: List[ExperienceCard] = []
        seen_titles: set[str] = set(existing_titles)
        for it in items:
            title_value = (it.get("title", "Untitled") or "").strip()
            norm_title = title_value.lower()
            if norm_title in seen_titles:
                continue
            seen_titles.add(norm_title)
            cards.append(ExperienceCard(
                title=title_value,
                description=it.get("description", ""),
                rationale=it.get("rationale"),
                confidence=float(it.get("confidence", 0.6)),
            ))
        # Save current batch to collection
        batch = [{
            "_id": c.id,
            "user_id": body.user_id,
            "title": c.title,
            "description": c.description,
            "rationale": c.rationale,
            "confidence": c.confidence,
            "created_at": now_iso(),
        } for c in cards]
        if batch:
            await db.experience_cards.insert_many(batch)
        return cards
    except Exception as e:
        logger.exception("OpenAI suggestion error")
        raise HTTPException(status_code=500, detail=f"Suggestion generation failed: {str(e)}")

# Swipe endpoint
class SwipeInput(BaseModel):
    user_id: str
    card_id: str
    direction: str  # right/left/up/down

@api_router.post("/placer/swipe", response_model=SwipeRecord)
async def placer_swipe(body: SwipeInput):
    if body.direction not in ["right", "left", "up", "down"]:
        raise HTTPException(status_code=400, detail="Invalid swipe direction")

    # check ownership
    card = await db.experience_cards.find_one({"_id": body.card_id, "user_id": body.user_id})
    if not card:
        raise HTTPException(status_code=404, detail="Card not found for this user")

    rec = SwipeRecord(user_id=body.user_id, card_id=body.card_id, direction=body.direction)
    await db.swipes.insert_one(rec.dict())
    return rec

# Fetch a page of cards (for swiper)
@api_router.get("/placer/cards", response_model=List[ExperienceCard])
async def placer_cards(user_id: str, limit: int = 10):
    # Exclude cards already swiped by this user
    swipes = await db.swipes.find({"user_id": user_id}).to_list(1000)
    swiped_ids = { s.get("card_id") for s in swipes }
    cursor = db.experience_cards.find({"user_id": user_id, "_id": {"$nin": list(swiped_ids)} }).sort("created_at", 1).limit(limit)
    docs = await cursor.to_list(length=limit)
    return [ExperienceCard(
        id=d["_id"],
        title=d.get("title", "Untitled"),
        description=d.get("description", ""),
        rationale=d.get("rationale"),
        confidence=float(d.get("confidence", 0.6)),
    ) for d in docs]

# Basic options provider
@api_router.get("/placer/options")
async def placer_options():
    return {
        "income_brackets": income_brackets_default,
        "education_levels": education_levels_default,
        "ethnicity_options": ethnicity_options_default,
    }

# Mount router
app.include_router(api_router)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()