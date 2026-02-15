from sqlalchemy.orm import Session
from ..models.user import User
from ..models.password_history import PasswordHistory
from ..schemas.user import UserCreate
from ..core.security import get_password_hash

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        hashed_password=hashed_password,
        is_active=user.is_active,
        trust_tier=user.trust_tier
    )
    db.add(db_user)
    db.flush()  # Flush to get the user ID

    # Store initial password in history
    password_history = PasswordHistory(
        user_id=db_user.id,
        hashed_password=hashed_password
    )
    db.add(password_history)

    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_password_history(db: Session, user_id: int, limit: int = 10):
    """Get the most recent password hashes for a user"""
    return db.query(PasswordHistory).filter(
        PasswordHistory.user_id == user_id
    ).order_by(PasswordHistory.created_at.desc()).limit(limit).all()

def check_password_reuse(db: Session, user_id: int, new_hashed_password: str, history_limit: int = 5):
    """Check if the new password matches any recent passwords in history"""
    recent_passwords = get_user_password_history(db, user_id, history_limit)
    return any(pw.hashed_password == new_hashed_password for pw in recent_passwords)

def add_password_to_history(db: Session, user_id: int, hashed_password: str):
    """Add a password to the user's history"""
    password_history = PasswordHistory(
        user_id=user_id,
        hashed_password=hashed_password
    )
    db.add(password_history)
    db.commit()
