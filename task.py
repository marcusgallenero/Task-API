from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3

class TaskCreate(BaseModel):
    title: str = ""
    done: bool = False

app = FastAPI()

DB_FILE = "tasks.db"

def get_connection():
    return sqlite3.connect(DB_FILE)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Create a table "tasks" if does not exist, with columns id, title, done
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks(
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            done INTEGER NOT NULL DEFAULT 0
            )
    """)
    conn.commit()

    # Add sample tasks if empty
    cursor.execute("SELECT COUNT (*) FROM tasks")
    count = cursor.fetchone()[0]
    if count == 0:
        cursor.executemany(
            "INSERT INTO tasks (title, done) VALUES (?, ?)",
            [
                ("wake up", 1),
                ("feed dog", 1),
                ("pet dog", 0)
            ]
        )
        conn.commit()

    conn.close()

init_db()

@app.get("/", summary="Display basic API information")
async def root():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": "[/tasks]"
    }

@app.get("/health", summary="Check if server is alive")
async def get_health():
    return {"status": "ok"}

@app.get("/tasks", summary="Return full list of tasks")
async def get_tasks():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tasks") # Inspect all columns from tasks
    rows = cursor.fetchall() # add sql data into Python as tuple
    conn.close()

    result = [
        {"id": row[0], "title": row[1], "done": bool(row[2])}
        for row in rows
    ]
    return result

@app.get("/tasks/{task_id}", summary="Return a single task by ID")
async def get_task(task_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id, ))
    row = cursor.fetchone() # Get row where id matches request
    conn.close()

    # Raise 404 if row with requested id not found
    if row is None:
        raise HTTPException(status_code=404, detail={"error": f"Task {task_id} not found"})
    return {"id": row[0], "title": row[1], "done": bool(row[2])}

@app.post("/tasks", status_code=201, summary="Create a new task")
async def create_task(new_task: TaskCreate):
    if not new_task.title.strip() or not new_task.title:
        raise HTTPException(status_code=400, detail={"error":"Bad Request"})

    task = {
        "id": len(tasks) + 1,
        "title": new_task.title,
        "done": new_task.done
    }

    tasks.append(task)
    return task

@app.put("/tasks/{task_id}", summary="Update task by ID")
async def update_task(task_id: int, updated_task: TaskCreate):
    if not updated_task.title.strip():
        raise HTTPException(status_code=400, detail={"error":"Bad Request"})

    for task in tasks:
        if task["id"] == task_id:
            task["title"] = updated_task.title
            task["done"] = updated_task.done
            return task
    raise HTTPException(status_code=404, detail={"error": f"Task {task_id} not found"})

@app.delete("/tasks/{task_id}", summary="Delete a task by ID")
async def delete_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            tasks.remove(task)
            return
    raise HTTPException(status_code=404, detail={"error": f"Task {task_id} not found"})