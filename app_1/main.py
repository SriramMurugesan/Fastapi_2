from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional
import json
import os

app = FastAPI(title="Student CRUD API with Dictionary Storage")

# JSON file path
JSON_FILE = "students.json"

# In-memory storage
students_db: Dict[int, dict] = {}
student_id_counter = {"current": 1}


# Helper functions for JSON persistence
def save_to_json():
    """Save the dictionary to JSON file"""
    data = {
        "students": students_db,
        "next_id": student_id_counter["current"]
    }
    with open(JSON_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_from_json():
    """Load the dictionary from JSON file"""
    global students_db, student_id_counter
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r") as f:
            data = json.load(f)
            students_db = {int(k): v for k, v in data.get("students", {}).items()}
            student_id_counter["current"] = data.get("next_id", 1)


# Load existing data on startup
load_from_json()


# Pydantic models
class Student(BaseModel):
    name: str
    email: str
    age: int
    course: str


class StudentResponse(BaseModel):
    id: int
    name: str
    email: str
    age: int
    course: str


# CRUD Functions
def create_student_func(student: Student) -> StudentResponse:
    student_id = student_id_counter["current"]
    student_data = student.model_dump()
    students_db[student_id] = student_data
    student_id_counter["current"] += 1
    save_to_json()
    return StudentResponse(id=student_id, **student_data)


def get_all_students_func() -> Dict[int, dict]:
    return students_db


def get_student_func(student_id: int) -> StudentResponse:
    if student_id not in students_db:
        raise HTTPException(status_code=404, detail="Student not found")
    return StudentResponse(id=student_id, **students_db[student_id])


def update_student_func(student_id: int, student: Student) -> StudentResponse:
    if student_id not in students_db:
        raise HTTPException(status_code=404, detail="Student not found")
    student_data = student.model_dump()
    students_db[student_id] = student_data
    save_to_json()
    return StudentResponse(id=student_id, **student_data)


def delete_student_func(student_id: int) -> dict:
    if student_id not in students_db:
        raise HTTPException(status_code=404, detail="Student not found")
    deleted_student = students_db.pop(student_id)
    save_to_json()
    return {"message": "Student deleted successfully", "deleted_student": deleted_student}


# Routes
@app.get("/")
def root():
    return {"message": "Student Management API with Dictionary Storage"}


@app.get("/storage")
def view_storage():
    """Display the internal dictionary storage for showcase purposes"""
    return {
        "students_db": students_db,
        "total_students": len(students_db),
        "next_id": student_id_counter["current"]
    }


@app.post("/students/", response_model=StudentResponse, status_code=201)
def create_student(student: Student):
    return create_student_func(student)


@app.get("/students/")
def get_all_students():
    return get_all_students_func()


@app.get("/students/{student_id}", response_model=StudentResponse)
def get_student(student_id: int):
    return get_student_func(student_id)


@app.put("/students/{student_id}", response_model=StudentResponse)
def update_student(student_id: int, student: Student):
    return update_student_func(student_id, student)


@app.delete("/students/{student_id}")
def delete_student(student_id: int):
    return delete_student_func(student_id)
