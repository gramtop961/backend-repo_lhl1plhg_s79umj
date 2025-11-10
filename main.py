import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents

app = FastAPI(title="LMS API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Helpers ----------

def oid(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id format")


def serialize(doc):
    if not doc:
        return doc
    d = {**doc}
    if "_id" in d:
        d["id"] = str(d.pop("_id"))
    # Convert datetime to isoformat
    for k, v in list(d.items()):
        if hasattr(v, "isoformat"):
            d[k] = v.isoformat()
    return d


# ---------- Schemas (request models) ----------
class CourseIn(BaseModel):
    title: str
    description: str
    instructor_id: str
    tags: Optional[List[str]] = []
    cover_image: Optional[str] = None
    level: Optional[str] = None


class LessonIn(BaseModel):
    course_id: str
    title: str
    content: Optional[str] = None
    video_url: Optional[str] = None
    order: int = 1


class EnrollmentIn(BaseModel):
    course_id: str
    user_id: str
    role: str = "student"


class AssignmentIn(BaseModel):
    course_id: str
    title: str
    description: Optional[str] = None
    due_date: Optional[str] = None
    max_points: int = 100


class SubmissionIn(BaseModel):
    assignment_id: str
    user_id: str
    content: Optional[str] = None


# ---------- Basic routes ----------
@app.get("/")
def root():
    return {"message": "LMS Backend is running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Connected & Working"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name
            response["connection_status"] = "Connected"
            response["collections"] = db.list_collection_names()
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response


# ---------- Courses ----------
@app.post("/api/courses")
def create_course(course: CourseIn):
    course_id = create_document("course", course.model_dump())
    doc = db["course"].find_one({"_id": ObjectId(course_id)})
    return serialize(doc)


@app.get("/api/courses")
def list_courses(q: Optional[str] = None, tag: Optional[str] = None, limit: int = 50):
    filt = {}
    if q:
        filt["title"] = {"$regex": q, "$options": "i"}
    if tag:
        filt["tags"] = tag
    docs = db["course"].find(filt).limit(limit)
    return [serialize(d) for d in docs]


@app.get("/api/courses/{course_id}")
def get_course(course_id: str):
    doc = db["course"].find_one({"_id": oid(course_id)})
    if not doc:
        raise HTTPException(404, "Course not found")
    return serialize(doc)


# ---------- Lessons ----------
@app.post("/api/lessons")
def create_lesson(lesson: LessonIn):
    lesson_id = create_document("lesson", lesson.model_dump())
    doc = db["lesson"].find_one({"_id": ObjectId(lesson_id)})
    return serialize(doc)


@app.get("/api/courses/{course_id}/lessons")
def list_lessons(course_id: str):
    docs = db["lesson"].find({"course_id": course_id}).sort("order", 1)
    return [serialize(d) for d in docs]


# ---------- Enrollments ----------
@app.post("/api/enrollments")
def enroll(enr: EnrollmentIn):
    # prevent duplicate enrollment
    existing = db["enrollment"].find_one({"course_id": enr.course_id, "user_id": enr.user_id})
    if existing:
        return serialize(existing)
    enr_id = create_document("enrollment", enr.model_dump())
    doc = db["enrollment"].find_one({"_id": ObjectId(enr_id)})
    return serialize(doc)


@app.get("/api/users/{user_id}/enrollments")
def user_enrollments(user_id: str):
    # For simplicity, just return enrollments; frontend can fetch courses separately.
    docs = db["enrollment"].find({"user_id": user_id})
    return [serialize(d) for d in docs]


# ---------- Assignments ----------
@app.post("/api/assignments")
def create_assignment(item: AssignmentIn):
    asg_id = create_document("assignment", item.model_dump())
    doc = db["assignment"].find_one({"_id": ObjectId(asg_id)})
    return serialize(doc)


@app.get("/api/courses/{course_id}/assignments")
def list_assignments(course_id: str):
    docs = db["assignment"].find({"course_id": course_id})
    return [serialize(d) for d in docs]


# ---------- Submissions ----------
@app.post("/api/submissions")
def submit(item: SubmissionIn):
    # upsert by user+assignment
    existing = db["submission"].find_one({"assignment_id": item.assignment_id, "user_id": item.user_id})
    data = item.model_dump()
    if existing:
        db["submission"].update_one({"_id": existing["_id"]}, {"$set": {**data}})
        doc = db["submission"].find_one({"_id": existing["_id"]})
        return serialize(doc)
    sub_id = create_document("submission", data)
    doc = db["submission"].find_one({"_id": ObjectId(sub_id)})
    return serialize(doc)


@app.get("/api/assignments/{assignment_id}/submissions")
def list_submissions(assignment_id: str):
    docs = db["submission"].find({"assignment_id": assignment_id})
    return [serialize(d) for d in docs]


# ---------- Schema exposure for builder tooling ----------
@app.get("/schema")
def get_schema():
    # Expose schemas file for tooling (simply echo available collection names)
    try:
        return {"collections": db.list_collection_names()}
    except Exception:
        return {"collections": []}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
