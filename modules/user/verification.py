"""
生成随机的验证码
"""
import secrets
from fastapi_mail import ConnectionConfig,FastMail,MessageSchema,MessageType
from core.config import settings

from redis.asyncio import Redis
#构建数据库连接池
redis_client = Redis.from_url(settings.redis_url,encoding="utf-8", decode_responses=True)

#根据邮箱获取Key，事实上Key现在还没有需要我们自己设计
def _key(email:str) -> str:
    #给注册功能申请验证码时，设计一个redis的key，这个key不能和其他功能重复
    return f"kb:register:code:{email.strip().lower()}"

#保存code数据到redis库中
async def save_code(email:str,code:str):
    await redis_client.set(_key(email),code,300)
#从数据库删除code
async def delete_code(email:str):
    await redis_client.delete(_key(email))
#用数据库验证code
async def verify_code(email:str,code:str):
    save_code = await redis_client.get(_key(email))
    return save_code is not None and secrets.compare_digest(save_code,code)



#生成一个4位整数随机验证码
def generate_code() -> str:
    return f"{secrets.randbelow(10_000):04d}"


def create_mail_instance() -> FastMail:

    config = ConnectionConfig(
        MAIL_USERNAME=settings.mail_username,
        MAIL_PASSWORD=settings.mail_password,
        MAIL_FROM=settings.mail_from,
        MAIL_PORT=settings.mail_port,
        MAIL_SERVER=settings.mail_server,
        MAIL_FROM_NAME=settings.mail_from_name,
        MAIL_STARTTLS=settings.mail_starttls,
        MAIL_SSL_TLS=settings.mail_ssl_tls,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True,
    )
    return FastMail(config)

async def send_code_email(email:str,code:str) -> None:
    message=MessageSchema(
        #主题
        subject="验证码",
        #内容
        body=f"您的验证码是：{code}",
        #收件人
        recipients=[email],
        #邮件类型
        subtype=MessageType.plain
    )
    await create_mail_instance().send_message(message)











