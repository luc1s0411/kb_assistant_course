from fastapi import APIRouter, Depends
from pydantic import EmailStr
from sqlalchemy.orm import Session

from modules.user.dependencies import get_current_user
from modules.user.model import User
from modules.user.repository import get_user_by_id

router = APIRouter(prefix="/auth", tags=["用户认证"])
from database.connection import get_session
from modules.user.service import request_verification_code
@router.get("/sendCode")
async def send_code(email: EmailStr,db:Session=Depends(get_session)):
    return await request_verification_code(email,db)

# 插入用户传递的数据
from modules.user.schemas import RegisterIn,CurrentUser,LoginIn,TokenOut
from modules.user.service import register_user,login_user,refresh_tokens,update_profile

@router.post("/register",response_model=CurrentUser)
async def register(userinfo: RegisterIn,db:Session=Depends(get_session)):
    # 调用serviece的代码存入数据
    return await register_user(db,userinfo)


@router.post("/login",response_model=TokenOut)
async def login(data:LoginIn,db:Session=Depends(get_session)):
    # 调用sevice实现登录
    return  login_user(db,data)

from modules.user.schemas import RefreshIn
@router.post("/refresh",response_model=TokenOut)
async def refresh(data: RefreshIn, db: Session = Depends(get_session)) -> TokenOut:
    return refresh_tokens(db, data)

@router.get("/me",response_model=CurrentUser)
async def me(user:CurrentUser=Depends(get_current_user)):
    return user

from modules.user.schemas import ProfileUpdateIn
@router.put("/me",response_model=CurrentUser)
def update_me(data: ProfileUpdateIn,
              user: CurrentUser = Depends(get_current_user),
              db: Session = Depends(get_session)):
    return update_profile(data, user, db)

