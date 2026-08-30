from sqlalchemy.orm import Session
from datetime import timedelta
from fastapi import HTTPException, status

from app.modules.auth.crud import AuthCRUD
from app.modules.auth.schemas import UserRegister, UserLogin
from app.core.security import Security
from app.core.config import settings

class AuthService:
    @staticmethod
    def register_user(db: Session, user_data: UserRegister) -> dict:
        if AuthCRUD.get_user_by_username(db, user_data.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        if AuthCRUD.get_user_by_email(db, user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        user = AuthCRUD.create_user(
            db=db,
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
            phone=user_data.phone
        )
        
        access_token = Security.create_access_token(data={"sub": str(user.id)})
        refresh_token = AuthCRUD.create_refresh_token(db, user.id)
        
        return {
            "user": user,
            "access_token": access_token,
            "refresh_token": refresh_token.token
        }
    
    @staticmethod
    def login_user(db: Session, login_data: UserLogin) -> dict:
        user = AuthCRUD.authenticate_user(db, login_data.username, login_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        AuthCRUD.update_last_login(db, user.id)
        
        access_token = Security.create_access_token(data={"sub": str(user.id)})
        refresh_token = AuthCRUD.create_refresh_token(db, user.id)
        
        return {
            "user": user,
            "access_token": access_token,
            "refresh_token": refresh_token.token
        }
    
    @staticmethod
    def refresh_access_token(db: Session, refresh_token: str) -> dict:
        db_token = AuthCRUD.get_refresh_token(db, refresh_token)
        if not db_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        access_token = Security.create_access_token(data={"sub": str(db_token.user_id)})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token
        }
    
    @staticmethod
    def logout_user(db: Session, refresh_token: str):
        AuthCRUD.revoke_refresh_token(db, refresh_token)
        return {"message": "Logged out successfully"}
