from .auth import get_current_user
from .schemas import TaskOut, TaskCreate
from fastapi import FastAPI, Depends, HTTPException
from .database import db, get_db_conn
from .schemas import UserCreate, UserOut
import asyncpg
from .security import hash_password, verify_password
from fastapi.security import OAuth2PasswordRequestForm
from  .auth import create_access_token
from typing import List
from fastapi import WebSocket, WebSocketDisconnect
from .websocket import manager

app = FastAPI(title = "Artemis Project")

@app.on_event("startup")
async def startup():
    await db.connect()
    async with db.pool.acquire() as connection:
        # User Table
        await connection.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                is_active BOOLEAN DEFAULT TRUE
            );
        ''')

        # Tasks Table
        await connection.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'Pending',
                owner_id INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT NOW()
            );
        ''')

        # Audit Table
        await connection.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                id SERIAL PRIMARY KEY,
                user_username TEXT,
                action TEXT,
                details TEXT,
                timestamp TIMESTAMP DEFAULT NOW()
            );
        ''')

@app.on_event("shutdown")
async def shutdown():
    await db.disconnect()

@app.post("/register", response_model=UserOut)
async def register_user(user:UserCreate, conn = Depends(get_db_conn)):
    existing_user = await conn.fetchrow("SELECT 1 FROM users WHERE username = $1 OR email = $2 LIMIT 1", user.username, user.email)
    if(existing_user):
        raise HTTPException(status_code=400, detail="Username or email already exists")

    # hashed_password = hash_password(user.password)

    new_user = await conn.fetchrow(
        """
        INSERT INTO users (username, email, hashed_password, role)
        VALUES ($1, $2, $3, $4) RETURNING id, username, email, role, is_active
        """,
        user.username, user.email, user.password, user.role
    )
    return dict(new_user)

@app.post("/login")
async def login_user(form_data: OAuth2PasswordRequestForm = Depends(), conn = Depends(get_db_conn)):
    user = await conn.fetchrow("SELECT 1 FROM users WHERE username = $1 LIMIT 1", form_data.username)

    # after fixing the hashing issue, we can verify thr password here
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token = create_access_token(data = {"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/tasks",response_model=TaskOut)
async def create_task(task: TaskCreate, current_user: dict = Depends(get_current_user) ,conn = Depends(get_db_conn)):
    if(current_user["role"] == "user"):
        raise HTTPException(status_code=403, detail="Only admins can create tasks")

    new_task = await conn.fetchrow("""
        INSERT INTO tasks (title, description, owner_id)
        VALUES ($1, $2, $3)
        RETURNING *
        """, task.title, task.description, task.owner_id)

    await conn.execute(
        "INSERT INTO audit_logs (user_username, action, details) VALUES ($1, $2, $3)",
        current_user['username'], "CREATE_TASK", f"Assigned task '{task.title}' to User ID {task.owner_id}"
    )

    await manager.send_message(f"New task assigned: {task.title} \n{task.description}", task.owner_id)

    return dict(new_task)


@app.get("/tasks", response_model=List[TaskOut])
async def get_tasks(
        current_user: dict = Depends(get_current_user),
        conn=Depends(get_db_conn)
):
    if current_user['role'] == 'admin':
        tasks = await conn.fetch("SELECT * FROM tasks")
    else:
        tasks = await conn.fetch("SELECT * FROM tasks WHERE owner_id = $1", current_user['id'])

    return [dict(task) for task in tasks]

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(websocket,user_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user_id)


