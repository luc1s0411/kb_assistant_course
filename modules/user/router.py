from fastapi import APIRouter, Depends
from pydantic import EmailStr
from sqlalchemy.orm import Session

from database.connection import get_session
from modules.user.schemas import RegisterIn, CurrentUser, TokenOut, LoginIn
from modules.user.service import request_verification_code, register_user, login_user

router = APIRouter(prefix="/auth", tags=["用户认证"])

from modules.user.verification import send_code_email,generate_code
@router.get("/sendCode")
async def send_code(email: EmailStr, db: Session = Depends(get_session)):
    return await request_verification_code(email, db)

@router.post("/register",response_model=CurrentUser)
async def register(userinfo: RegisterIn, db: Session = Depends(get_session)):
    # 调用service的代码存入数据
    return await register_user(db, userinfo)

@router.post("/login",response_model=TokenOut)
async def login(data:LoginIn, db: Session = Depends(get_session)):
    # 调用service实现登录
    return login_user(db, data)


@router.post("/refresh")
async def refresh():
    return 
