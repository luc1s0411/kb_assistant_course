from fastapi import APIRouter,Depends
from pydantic import EmailStr
from sqlalchemy.orm import Session
from database.connection import get_session
from modules.user.model import User
from modules.user.schemas import RegisterIn, CurrentUser, LoginIn, TokenOut, RefreshIn

router=APIRouter(prefix="/auth",tags=["用户认证"])

# from modules.user.verification import send_code_email,generate_code
from modules.user.service import request_verification_code, register_user
from modules.user.service import login_user


@router.get("/send_code")
async def send_code(email:EmailStr,db:Session=Depends(get_session)):
    # await send_code_email(email,generate_code())
    await request_verification_code(email,db)
    return {"message":f"验证码发送成功庆计时去{email}看"}


@router.post("/register",response_model=CurrentUser)
async def register(userinfo:RegisterIn,db:Session=Depends(get_session)):
    return await register_user(db,userinfo)

@router.post("/login",response_model=TokenOut)
async def login(data:LoginIn,db:Session=Depends(get_session)):
    return login_user(db,data)

from modules.user.service import refresh_tokens
@router.post("/refresh",response_model=TokenOut)
async def refresh(data:RefreshIn,db:Session=Depends(get_session)) -> TokenOut:
    return refresh_tokens(db,data)

from modules.user.dependencies import get_current_user
#使用依赖注入token解析me，获取数据
@router.get("/me",response_model=CurrentUser)
async def me(user:CurrentUser=Depends(get_current_user)):
    return user

from modules.user.service import updateprofile
from modules.user.schemas import ProfileUpdateIn

@router.put("/me",response_model=CurrentUser)
def updateme(data:ProfileUpdateIn,
             user:CurrentUser=Depends(get_current_user),
             db:Session=Depends(get_session)):
    return updateprofile(data,user,db)
from modules.user.schemas import updatePasswordIn
from modules.user.service import updatepasswordByID
@router.put("/me/password")
async def updatePassword(data:updatePasswordIn,
                   current_user:CurrentUser=Depends(get_current_user),
                   db:Session=Depends(get_session)):
    return updatepasswordByID(data,current_user,db)