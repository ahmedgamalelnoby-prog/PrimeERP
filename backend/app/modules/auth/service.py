from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.modules.auth.crud import AuthCRUD
from app.modules.auth.schemas import UserLogin, UserRegister
from app.core.security import Security

class AuthService:
    @staticmethod
    def login_user(db: Session, login_data: UserLogin):
        user = AuthCRUD.authenticate_user(db, login_data.username, login_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
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
    def register_user(db: Session, user_data: UserRegister):
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