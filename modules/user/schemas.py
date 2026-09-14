# from langchain_core.
from pydantic import BaseModel, Field, EmailStr, model_validator


# 定义一个类，指定用户传递那些信息
class RegisterIn(BaseModel):
    username: str=Field(min_length=1,max_length=10)
    email: EmailStr
    password: str
    confirm_password: str
    code:str
    full_name: str

    # 校验密码和确认密码一致
    @model_validator(mode='after')
    def password_match(self):
        if self.password != self.confirm_password:
            raise ValueError('Passwords do not match')
        return self

class CurrentUser(BaseModel):
    id: int
    username: str
    email: EmailStr
    full_name: str
    role: str
    permissions:set[str]

class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class LoginIn(BaseModel):
    account: str
    password: str