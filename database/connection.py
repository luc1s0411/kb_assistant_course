from collections.abc import Generator

from sqlalchemy import URL, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from core.config import settings

# 1.数据库的配置
databaseurl = URL.create(
    # 指定某台电脑的某个端口
    host=settings.db_host,
    port=settings.db_port,
    # 用户名，密码
    username=settings.db_user,
    password=settings.db_password,
    # 哪一个库
    database=settings.db_name,
    # 驱动
    drivername="mysql+pymysql",
    # 其它参数 字符集
    query={"charset": "utf8mb4"}
)
# 2.数据库引擎
engine = create_engine(databaseurl,
           # 数据库的连接，一次性开启几个，数据库连接池的大小
           pool_size=10,
           max_overflow=10,
           # 获取前测试连接有效性
           pool_pre_ping=True,
           # 多长时间不用，回收连接池中的连接
           pool_recycle=1800,
           # 如果多长时间没有连接到数据库，停止
           connect_args={'connect_timeout': 10})

# session工厂
sessionmaker = sessionmaker(
                            bind=engine,# 从哪一个连接池获取数据
                            class_=Session, # 连接类型
                            autoflush=False, # 是否自动刷新
                            expire_on_commit=False) # 是否提交事务
# 调用这个函数能够从连接池获取一个数据库的连接
def get_session():
    # 获取一个连接
    session = sessionmaker()
    try:
        yield session
    finally:
        session.close()