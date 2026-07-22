from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

class TaskCreate(BaseModel):
    title: str = ""
    done: bool = False

app = FastAPI()

tasks = [
    {
        "id": 1,
        "title": "wake up",
        "done": True
    },
    {
        "id": 2,
        "title": "feed dog",
        "done": True
    },
    {
        "id": 3,
        "title": "pet dog",
        "done": False
    }
]

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
    return tasks

@app.get("/tasks/{task_id}", summary="Return a single task by ID")
async def get_task(task_id: int):

    # Iterate through every task, return matching task
    for task in tasks:
        if task["id"] == task_id:
            return task
    raise HTTPException(status_code=404, detail={"error": f"Task {task_id} not found"})

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