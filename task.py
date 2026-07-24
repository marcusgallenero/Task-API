from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import psycopg
from dotenv import load_dotenv

load_dotenv() # Read .env and loads keys into environment

class TaskCreate(BaseModel):
    title: str = ""
    done: bool = False

app = FastAPI()

DB_URL = os.getenv("DATABASE_URL")

def get_connection():
    return psycopg.connect(DB_URL)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Create a table "tasks" if does not exist, with columns id, title, done
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks(
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            done BOOLEAN NOT NULL DEFAULT FALSE
            )
    """)
    conn.commit()

    # Add sample tasks if empty
    cursor.execute("SELECT COUNT (*) FROM tasks")
    count = cursor.fetchone()[0]
    if count == 0:
        cursor.executemany(
            "INSERT INTO tasks (title, done) VALUES (%s, %s)",
            [
                ("wake up", True),
                ("feed dog", True),
                ("pet dog", False)
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

    # Get task and row from tasks where id matches request
    cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id, ))
    row = cursor.fetchone()
    conn.close()

    # Raise 404 if row with requested id not found
    if row is None:
        raise HTTPException(status_code=404, detail={"error": f"Task {task_id} not found"})
    return {"id": row[0], "title": row[1], "done": bool(row[2])}

@app.post("/tasks", status_code=201, summary="Create a new task")
async def create_task(new_task: TaskCreate):
    if not new_task.title.strip() or not new_task.title:
        raise HTTPException(status_code=400, detail={"error":"Bad Request"})

    conn = get_connection()
    cursor = conn.cursor()

    # Add row in tasks with filled in title and done columns 
    cursor.execute(
        "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING *",
                   (new_task.title, new_task.done)
    )
    row = cursor.fetchone() # Get contents of new row
    conn.commit()
    conn.close()

    return {"id": row[0], "title": row[1], "done": row[2]}

@app.put("/tasks/{task_id}", summary="Update task by ID")
async def update_task(task_id: int, updated_task: TaskCreate):
    if not updated_task.title.strip():
        raise HTTPException(status_code=400, detail={"error":"Bad Request"})

    conn = get_connection()
    cursor = conn.cursor()

    # change title and done columns on row with specified id
    cursor.execute(
        "UPDATE tasks SET title = %s, done = %s WHERE id = %s",
        (updated_task.title, updated_task.done, task_id)
    )
    conn.commit()

    # raise error if no rows were changed
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail={"error": f"Task {task_id} not found"})
    conn.close()
    return {"id": task_id, "title":updated_task.title, "done": updated_task.done}

@app.delete("/tasks/{task_id}", status_code=204, summary="Delete a task by ID")
async def delete_task(task_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    # Delete task with specified id
    cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id, ))
    conn.commit()

    # raise error if no rows were changed
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail={"error": f"Task {task_id} not found"})
    conn.close()
    return 