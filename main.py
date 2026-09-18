from datetime import datetime, timedelta, timezone
from typing import List, Optional
import uuid

from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi.responses import JSONResponse

from config import settings
from database import get_db_session, async_session
from models import User, Match, MatchEvent, MatchStatus, EventType
from websocket_manager import manager
from services.ai_forge import generate_challenge
from services.compiler import submit_code
from services.shoutcaster import generate_shoutcast
from services.solo_challenges import challenge_for, level_from_xp, public_challenge

app = FastAPI(title="AlgoArena Backend", description="Real-time 1v1 Competitive Coding Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://*.github.io", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
        headers={"Access-Control-Allow-Origin": "*"}
    )

# --- Schemas ---
class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    college_campus: Optional[str] = None
    academic_section: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class CodeSubmitRequest(BaseModel):
    match_id: str
    user_id: str
    source_code: str
    language: str

class SoloStartRequest(BaseModel):
    mode: str = "practice"

# --- Auth Utils ---
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

async def current_user(authorization: Optional[str] = Header(None), db: AsyncSession = Depends(get_db_session)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Please log in first")
    try:
        payload = jwt.decode(authorization.split(" ", 1)[1], settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id = uuid.UUID(payload.get("sub", ""))
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Your session has expired")
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# --- REST Endpoints ---
@app.post("/api/auth/register", response_model=Token)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db_session)):
    query = select(User).where(User.username == req.username)
    result = await db.execute(query)
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Username already registered")
        
    new_user = User(
        username=req.username,
        email=req.email,
        hashed_password=pwd_context.hash(req.password),
        college_campus=req.college_campus,
        academic_section=req.academic_section,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    token = create_access_token({"sub": str(new_user.id)})
    return {"access_token": token, "token_type": "bearer"}

@app.post("/api/auth/login", response_model=Token)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db_session)):
    result = await db.execute(select(User).where(User.username == req.username))
    user = result.scalars().first()
    if not user or not pwd_context.verify(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
        
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/api/user/me")
async def get_me(user: User = Depends(current_user)):
    level = level_from_xp(user.xp)
    if user.level != level:
        user.level = level
    return {"id": str(user.id), "username": user.username, "elo_rating": user.elo_rating,
            "xp": user.xp, "level": level, "total_solved": user.total_solved,
            "current_streak": user.current_streak, "xp_to_next": level * level * 120}

@app.post("/api/solo/start")
async def start_solo(req: SoloStartRequest, user: User = Depends(current_user), db: AsyncSession = Depends(get_db_session)):
    level = level_from_xp(user.xp)
    challenge = challenge_for(req.mode, level)
    match = Match(status=MatchStatus.active, player1_id=user.id, problem_data=challenge)
    db.add(match)
    await db.commit()
    await db.refresh(match)
    return {"match_id": str(match.id), "problem": public_challenge(challenge), "bot": challenge["bot"]}

@app.get("/api/leaderboard")
async def get_leaderboard(campus: Optional[str] = None, section: Optional[str] = None, db: AsyncSession = Depends(get_db_session)):
    query_str = """
    SELECT 
        username, 
        elo_rating, 
        RANK() OVER (ORDER BY elo_rating DESC) as global_rank,
        RANK() OVER (PARTITION BY college_campus ORDER BY elo_rating DESC) as campus_rank,
        RANK() OVER (PARTITION BY academic_section ORDER BY elo_rating DESC) as section_rank
    FROM users 
    WHERE 1=1
    """
    params = {}
    if campus:
        query_str += " AND college_campus = :campus"
        params["campus"] = campus
    if section:
        query_str += " AND academic_section = :section"
        params["section"] = section
    
    query_str = f"SELECT * FROM ({query_str}) AS ranked ORDER BY global_rank LIMIT 100"
    
    result = await db.execute(text(query_str), params)
    return result.mappings().all()

@app.post("/api/match/submit")
async def submit_match_code(req: CodeSubmitRequest, db: AsyncSession = Depends(get_db_session)):
    # 1. Fetch match and problem data
    result = await db.execute(select(Match).where(Match.id == uuid.UUID(req.match_id)))
    match_obj = result.scalars().first()
    if not match_obj:
        raise HTTPException(status_code=404, detail="Match not found")
        
    if match_obj.status != MatchStatus.active:
        raise HTTPException(status_code=400, detail="Match is not active")
        
    test_cases = match_obj.problem_data.get("test_cases", [])
    inputs = [tc.get("input", "") for tc in test_cases]
    expected_outputs = [tc.get("expected_output", "") for tc in test_cases]
    
    # 2. Run compiler service
    results = await submit_code(req.source_code, req.language, inputs, expected_outputs)
    
    # 3. Evaluate results
    passed_all = bool(results) and all(r.get("status") == "Accepted" for r in results)
    has_compile_error = any(r.get("status", "").startswith("Compilation Error") for r in results)
    
    # 4. Generate Shoutcaster comment
    if passed_all:
        shoutcast_prompt = f"Player {req.user_id} just passed all test cases flawlessly!"
        event_type = EventType.test_passed
    elif has_compile_error:
        shoutcast_prompt = f"Player {req.user_id} just hit a massive compilation error!"
        event_type = EventType.compile_error
    else:
        shoutcast_prompt = f"Player {req.user_id} failed some test cases on their submission."
        event_type = EventType.test_passed  # Used generally for execution runs

    try:
        commentary = await generate_shoutcast(shoutcast_prompt)
    except Exception:
        commentary = "Clean execution! The arena is watching your next move."
    
    # 5. Log Event & Update Match
    event = MatchEvent(
        match_id=match_obj.id,
        user_id=uuid.UUID(req.user_id),
        event_type=event_type,
        payload={"results": results, "commentary": commentary}
    )
    db.add(event)
    
    if passed_all:
        match_obj.status = MatchStatus.completed
        match_obj.winner_id = uuid.UUID(req.user_id)
        match_obj.finished_at = datetime.now(timezone.utc)
        player = await db.get(User, uuid.UUID(req.user_id))
        if player:
            reward = int(match_obj.problem_data.get("xp_reward", 45))
            player.xp += reward
            player.total_solved += 1
            player.current_streak += 1
            player.level = level_from_xp(player.xp)
            
            # Multiplayer Elo logic
            if match_obj.player2_id is not None:
                player.elo_rating += 25
                loser_id = match_obj.player1_id if match_obj.player2_id == player.id else match_obj.player2_id
                loser = await db.get(User, loser_id)
                if loser:
                    loser.elo_rating = max(0, loser.elo_rating - 15)
    
    await db.commit()
    
    # 6. Broadcast event via WebSockets
    await manager.broadcast_to_match(req.match_id, {
        "type": "code_submission",
        "user_id": req.user_id,
        "passed": passed_all,
        "commentary": commentary,
        "match_completed": passed_all
    })
    
    progression = None
    if passed_all and player:
        progression = {"xp": player.xp, "level": player.level, "reward": reward,
                       "xp_to_next": player.level * player.level * 120}
    return {"passed": passed_all, "commentary": commentary, "results": results, "progression": progression}

# --- WebSockets ---
@app.websocket("/ws/arena/{match_id}/{user_id}")
async def arena_websocket(websocket: WebSocket, match_id: str, user_id: str):
    if match_id == "matchmaking":
        await websocket.accept()
        pair_info = await manager.join_matchmaking(websocket, user_id)
        
        if pair_info:
            new_match_id, opponent_id, opponent_ws = pair_info
            
            # Generate Problem Data via Gemini
            problem_data = await generate_challenge("Dynamic Programming or Graph Theory")
            
            # Create Match in DB
            async with async_session() as db:
                new_match = Match(
                    id=uuid.UUID(new_match_id),
                    status=MatchStatus.active,
                    player1_id=uuid.UUID(opponent_id),
                    player2_id=uuid.UUID(user_id),
                    problem_data=problem_data
                )
                db.add(new_match)
                await db.commit()
            
            # Notify both players
            msg = {
                "type": "match_found", 
                "match_id": new_match_id,
                "problem": problem_data
            }
            await opponent_ws.send_json(msg)
            await websocket.send_json(msg)
            
            # Close matchmaking sockets so clients reconnect to the actual match_id
            await opponent_ws.close()
            await websocket.close()
            return
        else:
            await websocket.send_json({"type": "waiting_in_queue"})
            try:
                while True:
                    await websocket.receive_text()
            except WebSocketDisconnect:
                if user_id in manager.waiting_queue:
                    del manager.waiting_queue[user_id]
                return

    # Regular match room
    await manager.connect(websocket, match_id)
    try:
        while True:
            data = await websocket.receive_json()
            # Relay messages like keystrokes or emotes
            await manager.broadcast_to_match(match_id, {"user_id": user_id, "data": data})
    except WebSocketDisconnect:
        manager.disconnect(websocket, match_id)
        await manager.broadcast_to_match(match_id, {"type": "player_disconnected", "user_id": user_id})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
