import streamlit as st
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from db.models import SessionLocal, User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)

def signup(username: str, password: str) -> bool:
    db: Session = SessionLocal()
    if db.query(User).filter(User.username == username).first():
        return False
    user = User(username=username, hashed_password=hash_password(password))
    db.add(user)
    db.commit()
    return True

def login(username: str, password: str) -> bool:
    db: Session = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    return verify_password(password, user.hashed_password)
