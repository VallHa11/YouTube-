from ninja import Schema
from typing import Optional
from datetime import datetime
from typing import List


class VideoOut(Schema):
    id: int
    title: str
    description: Optional[str]
    video_file: str
    thumbnail: Optional[str]
    author_id: int
    uploaded_at: datetime
    views: int
    likes: int
    dislikes: int

class RegisterSchema(Schema):
    username: str
    password: str
    email: Optional[str]

class LoginSchema(Schema):
    username: str
    password: str

class CommentIn(Schema):
    text: str

class CommentOut(Schema):
    id: int
    author_id: int
    text: str
    created_at: datetime

class SimpleVideo(Schema):
    id: int
    title: str
    uploaded_at: datetime

class UserProfileOut(Schema):
    id: int
    username: str
    email: Optional[str]
    bio: Optional[str] = None
    avatar: Optional[str] = None
    subscribers_count: int
    subscriptions_count: int
    videos: List[SimpleVideo]

class ProfileUpdateIn(Schema):
    email: Optional[str]
    bio: Optional[str]

class SimpleUser(Schema):
    id: int
    username: str
    avatar: Optional[str]
    bio: Optional[str]

