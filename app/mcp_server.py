from fastapi.params import Depends
from fastmcp import FastMCP
from app.database import db
from app.config import settings
import asyncpg

mcp = FastMCP("Artimes Intelligence")

DATABASE_URL = settings.DATABASE_URL

@mcp.tool()
async def get_audit_logs(limit: int =10):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        rows = await conn.fetch(
            "SELECT user_username, action, details, timestamp FROM audit_logs ORDER BY timestamp DESC LIMIT $1",
            limit
        )
        return [dict(row) for row in rows]
    finally:
        await conn.close()

@mcp.tool()
async def list_open_tasks():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        rows = await conn.fetch(
            "SELECT id, title, status, owner_id FROM tasks WHERE status != 'Done'"
        )
        return [dict(row) for row in rows]
    finally:
        await conn.close()

@mcp.tool()
async def analyse_user_workload(user_id: int):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        rows = await conn.fetch(
            """
            SELECT title, description
            FROM tasks
            WHERE owner_id = $1
              AND status != 'Done'
            """,
            user_id,
        )

        tasks = [dict(row) for row in rows]
        user = await conn.fetchrow("SELECT username FROM users WHERE id = $1", user_id)
        username = user['username'] if user else f"User {user_id}"

        return {
            "user_id": user_id,
            "username": username,
            "pending_tasks": tasks,
            "open_taks_count": len(tasks),
        }

    finally:
        await conn.close()


if __name__ == "__main__":
    mcp.run()