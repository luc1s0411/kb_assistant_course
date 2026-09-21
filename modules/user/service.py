from fastapi import HTTPException
from modules.user.verification import *
from sqlalchemy.orm import Session
from modules.user.repository import get_user_by_email, get_perssion
from core.security import hash_password
#service是存放业务代码的文件，

#发送邮件并保存到redias
async def request_verification_code(email: str,db):
    if get_user_by_email(db,email):
        raise HTTPException(status_code=503, detail="该邮箱已注册")
    try:
        code = generate_code()
        #发送邮件，存入redis
        await send_code_email(email,code)
        await save_code(email, code)
        return {"message": "验证码已发送，请查收"}

    except Exception as e:
        return {"message": str(e)}

from modules.user.model import User
from modules.user.schemas import RegisterIn, CurrentUser
from modules.user.repository import create_user
from datetime import datetime

def to_current_user(db:Session,user:User):
    return CurrentUser(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role_code,
        permissions=get_perssion(db,int(user.id))
    )
async def register_user(db:Session,userinfo:RegisterIn):
    try:
        #1.校验
        #1.1邮箱校验：如果改邮箱已经注册，告诉用户换一个邮箱，
        if get_user_by_email(db,userinfo.email):
            raise HTTPException(status_code=503, detail="该邮箱已注册，请更换邮箱")

        if not await verify_code(userinfo.email, userinfo.code):
            raise HTTPException(status_code=503, detail="验证码错误")
        #2.
        user = User(
            username=userinfo.username,
            email=userinfo.email,
            password_hash=hash_password(userinfo.password),
            role_code="public",
            created_at=datetime.now(),
            full_name=userinfo.full_name,
                    )
        create_user(db,user)
        await delete_code(userinfo.email)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return to_current_user(db,user)

from core.security import create_token_pair
from modules.user.schemas import TokenOut
def _token_out(row) -> TokenOut:
    access_token,refresh_token=create_token_pair(int(row.id),str(row.role_code))
    return TokenOut(access_token=access_token, refresh_token=refresh_token)

from modules.user.schemas import LoginIn
from core.security import verify_password

def login_user(db:Session,data:LoginIn):

    user:User = get_user_by_email(db,data.account)

    if not user or not verify_password(data.password, str(user.password_hash)):
        raise HTTPException(status_code=401, detail="账号或密码错误")


    if not user.is_active:
        raise HTTPException(status_code=401, detail="账号已禁用")
    return _token_out(user)

from core.security import decode_refresh_token
from modules.user.repository import get_user_by_id
from modules.user.schemas import RefreshIn

def refresh_tokens(db: Session, data: RefreshIn) -> TokenOut:
    user_id, token_role = decode_refresh_token(data.refresh_token)
    user: User = get_user_by_id(db, user_id)
    if user is None or not user.is_active or user.role_code != token_role:
        raise HTTPException(
            status_code=401,
            detail="用户不存在、已停用或角色已变更",
        )
    return _token_out(user)

from modules.user.repository import update_user_profile
from modules.user.schemas import ProfileUpdateIn
def updateprofile(data:ProfileUpdateIn,
                  user:CurrentUser,
                  db:Session):
    myuser=update_user_profile(data,user,db)
    return to_current_user(db,myuser)

from modules.user.schemas import updatePasswordIn
from modules.user.repository import update_password_hash
def updatepasswordByID(data:updatePasswordIn,
                    user:CurrentUser,
                    db:Session):
    #1.校验
    user=get_user_by_id(db,user.id)
    #2.密码是否正确
    if not verify_password(data.current_password, str(user.password_hash)):
        raise HTTPException(status_code=401, detail="原密码错误")
    if data.current_password == data.new_password:
        raise HTTPException(status_code=401, detail="新密码不能与原密码相同")

    #更新
    if not update_password_hash(db,user.id,hash_password(data.new_password)):
        raise HTTPException(status_code=401,detail="密码更新失败")
    return {"message":"密码更新成功"}