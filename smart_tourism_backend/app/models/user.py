from sqlalchemy import Column, Integer, String, JSON

from app.models.common import Base, TimeStampedMixin


class User(Base, TimeStampedMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    email = Column(String(128), unique=True, index=True, nullable=True)
    hashed_password = Column(String(256), nullable=False)

    # Basic preferences (simple structured fields)
    preferences = Column(JSON, nullable=True)

    # Link to profile vector in vector DB (e.g., Milvus)
    profile_vector_id = Column(String(64), nullable=True)

