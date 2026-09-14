import secrets

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

from core.config import settings

from redis.asyncio import Redis

# 构建数据库连接池,redis库默认取出的连接就是从连接池取的，所以，事实上一般不用关闭
redis_client = Redis.from_url(settings.redis_url,encoding="utf-8",decode_responses=True)

# 根据邮箱获取key。事实上，key现在还没有，我们自己去设计
def _key(email: str) -> str:
    # 给注册功能申请验证码时，设计一个redis的key，这个key注意不和其它功能冲突
    return f"kb:register:code:{email.strip().lower()}"

# 保存code数据到redis库
async def save_code(email:str,code:str):
    await redis_client.set(_key(email),code,ex=300)

# 删除code从数据库
async def delete_code(email:str):
    await redis_client.delete(_key(email))

# 验证code
async def verify_code(email:str,code:str):
    save_code = await redis_client.get(_key(email))
    # 判断你传递过来的code和我数据库中的code是否是相等的
    # save_code == code
    return save_code is not None and secrets.compare_digest(save_code,code)
# 1.生成随机数的验证码
def generate_code() -> str:
    # random.random   小于1万  0-9999   0090
    # {:.2f}
    return f"{secrets.randbelow(10_000):04d}"

# 2.准备FastMail这个对象，因为需要这个对象发射验证码
def create_mail_instance() -> FastMail:
    # 对必须加的配置，加上，如果没有必须的任何配置直接报错
    required = {
        "MAIL_USERNAME": settings.mail_username,
        "MAIL_PASSWORD": settings.mail_password,
        "MAIL_FROM": settings.mail_from,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise RuntimeError(f"缺少 QQ 邮箱配置：{', '.join(missing)}")


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

# message = MessageSchema(
#         subject="Fastapi-Mail module",
#         recipients=email.dict().get("email"),
#         body=html,
#         subtype=MessageType.html)
#
#     fm = FastMail(conf)
#     await fm.send_message(message)

async def send_code_email(email: str, code: str) -> None:
    message = MessageSchema(
        # 主题
        subject="【知识库智能助手】注册验证码",
        # 发送给那个邮箱，可以同时发送给多人
        recipients=[email],
        # 内容
        body=f"您的注册验证码为：{code}，请在 5 分钟内使用。",
        # 类型  plain是字符串的意思
        subtype=MessageType.plain,
    )
    await create_mail_instance().send_message(message)

