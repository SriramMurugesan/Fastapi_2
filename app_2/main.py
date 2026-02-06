from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import List

# Database setup
DATABASE_URL = "sqlite:///./students.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI(title="Student CRUD API with SQLite")


# SQLAlchemy Model
class StudentModel(Base):
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    course = Column(String, nullable=False)


# Create tables
Base.metadata.create_all(bind=engine)


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
    
    class Config:
        from_attributes = True


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# CRUD Functions
def create_student_func(student: Student, db: Session) -> StudentResponse:
    db_student = StudentModel(**student.model_dump())
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return StudentResponse.model_validate(db_student)


def get_all_students_func(db: Session) -> List[StudentResponse]:
    students = db.query(StudentModel).all()
    return [StudentResponse.model_validate(student) for student in students]


def get_student_func(student_id: int, db: Session) -> StudentResponse:
    student = db.query(StudentModel).filter(StudentModel.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return StudentResponse.model_validate(student)


def update_student_func(student_id: int, student: Student, db: Session) -> StudentResponse:
    db_student = db.query(StudentModel).filter(StudentModel.id == student_id).first()
    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    for key, value in student.model_dump().items():
        setattr(db_student, key, value)
    
    db.commit()
    db.refresh(db_student)
    return StudentResponse.model_validate(db_student)


def delete_student_func(student_id: int, db: Session) -> dict:
    db_student = db.query(StudentModel).filter(StudentModel.id == student_id).first()
    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    student_data = StudentResponse.model_validate(db_student)
    db.delete(db_student)
    db.commit()
    return {"message": "Student deleted successfully", "deleted_student": student_data}


# Routes
@app.get("/")
def root():
    return {"message": "Student Management API with SQLite Database"}


@app.post("/students/", response_model=StudentResponse, status_code=201)
def create_student(student: Student, db: Session = Depends(get_db)):
    return create_student_func(student, db)


@app.get("/students/", response_model=List[StudentResponse])
def get_all_students(db: Session = Depends(get_db)):
    return get_all_students_func(db)


@app.get("/students/{student_id}", response_model=StudentResponse)
def get_student(student_id: int, db: Session = Depends(get_db)):
    return get_student_func(student_id, db)


@app.put("/students/{student_id}", response_model=StudentResponse)
def update_student(student_id: int, student: Student, db: Session = Depends(get_db)):
    return update_student_func(student_id, student, db)


@app.delete("/students/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db)):
    return delete_student_func(student_id, db)
