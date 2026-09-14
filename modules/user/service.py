from datetime import datetime

from fastapi import HTTPException

from core.security import hash_password, verify_password
from modules.user.repository import get_user_by_email
# service是存放业务代码的文件
from modules.user.verification import generate_code, save_code, send_code_email, verify_code, delete_code
from sqlalchemy.orm import Session
# 发送邮件，并存储到redis
from modules.user.verification import send_code_email
async def request_verification_code(email:str, db = Session):
    # 如果这个邮箱已经注册过，我们是没必要继续发邮件，直接提醒用户，该邮箱已经注册
    # #这个业务需求，翻译成技术。就是拿邮箱去数据库中查询，如果有，说明注册过
    # 告诉用户，该邮箱已经注册，如果没继续走下一个流程
    if get_user_by_email(db, email):
        raise HTTPException(status_code=503,detail="该邮箱已经注册，请更换")
    try:
        code = generate_code()
        # 1.发送邮件
        await send_code_email(email,code)
        # 2.存入redis
        await save_code(email,code)
    except Exception as err:
        print(err)
    return {"message":f"验证码发送成功，请及时去邮箱{email}查看"}


from modules.user.schemas import RegisterIn, CurrentUser, TokenOut
from modules.user.model import User
from modules.user.repository import create_user,get_perssion

def to_current_user(db: Session, user:User):
    return CurrentUser(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role.name,
        permissions=get_perssion(db,int(user.id))
    )

async def register_user(db:Session,userinfo: RegisterIn):
    # 1.校验
    # 1.1 邮箱校验：如果该邮箱已经注册，告诉用户换一个邮箱
    if get_user_by_email(db, userinfo.email):
        raise HTTPException(status_code=503,detail="该邮箱已经注册，请更换")

    # 1.2 验证码校验
    if not await verify_code(userinfo.email,userinfo.code):
        raise HTTPException(status_code=503,detail="验证码错误，请核对后重试")

    user = User(username=userinfo.username,
                email=userinfo.email,
                password_hash=hash_password(userinfo.password),
                role_code="public",
                is_active=True,
                created_at=datetime.now(),
                full_name=userinfo.full_name
                )
    create_user(db,user)
    # 验证码使用后作废，防止重放
    await delete_code(userinfo.email)
    return to_current_user(db,user)

from core.security import create_token_pair

def _token_out(row) -> TokenOut:
    access_token,refresh_token = create_token_pair(
        int(row.id),
        str(row.role_code)
    )
    return TokenOut(access_token=access_token,refresh_token=refresh_token)

from modules.user.schemas import LoginIn
def login_user(db:Session,data: LoginIn):

    user:User = get_user_by_email(db, data.account)
    if user is None or not verify_password(data.password, str(user.password_hash)):
        raise HTTPException(
            status_code=401,
            detail="账号或密码错误",
        )
    # 如果用户没激活
    if not user.is_active:
        raise HTTPException(status_code=403, detail="用户已停用")
    return _token_out(user)