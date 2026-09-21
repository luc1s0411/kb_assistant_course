
from pydantic import BaseModel, Field, EmailStr, model_validator, ValidationError


#定义一个类，指定用户传递信息

class RegisterIn(BaseModel):
    username:str=Field(min_length=2,max_length=20)
    email:EmailStr
    password:str=Field(min_length=8,max_length=30)
    confirm_password:str=Field(min_length=8,max_length=30)
    code:str
    full_name:str

    @model_validator(mode='after')
    def password_match(self):
        if self.password != self.confirm_password:
            raise ValidationError('Passwords do not match')
        return self

class CurrentUser(BaseModel):
    id:int
    username:str
    email:EmailStr
    full_name:str
    role:str
    permissions:set[str]

class LoginIn(BaseModel):
    account:str
    password:str

class TokenOut(BaseModel):
    access_token:str
    refresh_token:str
    token_type:str="bearer"

class RefreshIn(BaseModel):
    refresh_token:str=Field(min_length=20)

class ProfileUpdateIn(BaseModel):
    username:str|None = Field(None)
    email:str|None = Field(None)
    full_name:str|None = Field(None)

class updatePasswordIn(BaseModel):
    current_password:str
    new_password:str