"""
Database Schemas for LMS

Each Pydantic model represents a collection in MongoDB.
Collection name is the lowercase class name (e.g., Course -> "course").
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime

# -------- Core Entities --------

class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Email address")
    role: str = Field("student", description="Role: student | instructor | admin")
    avatar_url: Optional[str] = Field(None, description="Avatar image URL")
    bio: Optional[str] = Field(None, description="Short bio")

class Course(BaseModel):
    title: str = Field(..., description="Course title")
    description: str = Field(..., description="Course description")
    instructor_id: str = Field(..., description="Creator user id")
    tags: List[str] = Field(default_factory=list, description="Keywords")
    cover_image: Optional[str] = Field(None, description="Cover image URL")
    level: Optional[str] = Field(None, description="Level: beginner/intermediate/advanced")

class Lesson(BaseModel):
    course_id: str = Field(..., description="Parent course id")
    title: str = Field(..., description="Lesson title")
    content: Optional[str] = Field(None, description="Rich text/markdown content")
    video_url: Optional[str] = Field(None, description="Video URL")
    order: int = Field(1, ge=1, description="Display order")

class Enrollment(BaseModel):
    course_id: str = Field(..., description="Course id")
    user_id: str = Field(..., description="User id")
    role: str = Field("student", description="student | ta | instructor")

class Announcement(BaseModel):
    course_id: str = Field(..., description="Course id")
    title: str = Field(..., description="Announcement title")
    message: str = Field(..., description="Announcement body")

class Assignment(BaseModel):
    course_id: str = Field(..., description="Course id")
    title: str = Field(..., description="Assignment title")
    description: Optional[str] = Field(None, description="Assignment description")
    due_date: Optional[datetime] = Field(None, description="Due date")
    max_points: int = Field(100, ge=1, description="Maximum points")

class Submission(BaseModel):
    assignment_id: str = Field(..., description="Assignment id")
    user_id: str = Field(..., description="User id")
    content: Optional[str] = Field(None, description="Submitted content / link")
    grade: Optional[float] = Field(None, ge=0, description="Grade awarded")
    feedback: Optional[str] = Field(None, description="Instructor feedback")

# Note: The Flames database viewer will automatically read these via GET /schema
