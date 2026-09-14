from openai.types.admin.organization import role
from sqlalchemy.orm import Session
from modules.user.model import User, Permission, role_permissions
from sqlalchemy import select
# 访问数据库的文件
#通过邮箱查询用户是否存在
def get_user_by_email(db:Session,email:str):
    # select * from user where user.email=email
    return db.scalar(select(User).where(User.email == email))

def get_user_by_id(db:Session,user_id:int):
    # select * from user where user.id=id
    return db.scalar(select(User).where(User.id == user_id))
# 定义向user表插入一条数据的函数

def create_user(db:Session,user:User):
    db.add(user)
    db.commit()
    db.refresh(user)

#获取该用户的权限code
def get_perssion(db:Session,id:int):
    #  Table 表在联合查询是加一个.c
    codes = db.scalars(select(Permission.code).
                       join(role_permissions,Permission.code
                             == role_permissions.c.permission_code).
               join(User,User.role_code == role_permissions.c.role_code)
               .where(User.id == id,User.is_active.is_(True))).all()
    return set(codes)

