from datetime import datetime

from fastapi import HTTPException
# sevice是存放业务代码的文件
from modules.user.verification import generate_code,save_code,send_code_email
from sqlalchemy.orm import Session
# 发送邮件，并存储到redis
from modules.user.verification import send_code_email
from modules.user.repository import get_user_by_email
async def request_verification_code(email:str,db:Session):

    # 如果这个邮箱已经注册过，我们是没必要继续发邮件，直接提醒用户，该邮箱已经注册
    # 这个业务需求，翻译成技术。就是拿邮箱去数据库中查询，如果有，说明注册过
    # 告诉用户，该邮箱已经注册，如果没有，继续走下一个流程
    if get_user_by_email(db,email):
        raise HTTPException(status_code=503,detail="该邮箱已注册，请更换")
    try:
        code = generate_code()
        # 1.发送邮件
        await send_code_email(email,code)
        # 2.存入redis
        await save_code(email,code)
    except Exception as err:
        print(err)
    return {"message":f"验证码发送成功，请及时去邮箱{email}查看"}

from modules.user.schemas import RegisterIn, CurrentUser
from modules.user.model import  User
from modules.user.repository import create_user,get_perssion
from modules.user.verification import verify_code,delete_code
from core.security import verify_password,hash_password

def to_current_user(db:Session,user:User):
    return CurrentUser(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role.name,
        permissions=get_perssion(db,int(user.id))
    )

async def register_user(db:Session,userinfo: RegisterIn):
    try:
        # 1.校验
        # 1.1邮箱校验：如果该邮箱已经注册，告诉用户换一个邮箱
        # 拿邮箱去数据库中查，看看有没有，如果有就是已经注册过
        if get_user_by_email(db, userinfo.email):
            raise HTTPException(status_code=503, detail="该邮箱已注册，请更换")
        # 1.2验证码校验
        # 技术：redis中验证码有没有
        if not await verify_code(userinfo.email,userinfo.code):
            raise HTTPException(status_code=503, detail="验证码错误，请核对后重试")

        user = User(username=userinfo.username,
             email=userinfo.email,
             password_hash=hash_password(userinfo.password),
             role_code="public",
             is_active=True,
             created_at=datetime.now(),
             full_name=userinfo.full_name,
             )
        create_user(db,user)
        await delete_code(userinfo.email)
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))
    return to_current_user(db,user)

from modules.user.schemas import TokenOut

from core.security import create_token_pair

def _token_out(row) -> TokenOut:
    access_token, refresh_token = create_token_pair(
        int(row.id),
        str(row.role_code),
    )
    return TokenOut(access_token=access_token, refresh_token=refresh_token)

from modules.user.schemas import LoginIn,RefreshIn
def login_user(db: Session, data: LoginIn):

    user:User = get_user_by_email(db, data.account)
    # if user is None  如果你不是我的会员  或者你的密码不多
    if user is None or not verify_password(data.password, str(user.password_hash)):
        raise HTTPException(
            status_code=401,
            detail="账号或密码错误",
        )
    # 如果用户没激活
    if not user.is_active:
        raise HTTPException(status_code=403, detail="用户已停用")
    return _token_out(user)

from core.security import decode_refresh_token
from modules.user.repository import get_user_by_id

def refresh_tokens(db: Session, data: RefreshIn) -> TokenOut:

    user_id, token_role = decode_refresh_token(data.refresh_token)

    user:User = get_user_by_id(db, user_id)
    if user is None or not user.is_active or user.role_code != token_role:
        raise HTTPException(
            status_code=401,
            detail="用户不存在、已停用或角色已变更",
        )
    return _token_out(user)