import redis

redis_url="redis://127.0.0.1:6379"
#1.连接库
redis_client=redis.from_url(redis_url,encoding="utf-8",
                            #告诉客户端，数据自动解析成字符串
                            decode_responses=True)
#2.设置值
redis_client.set("name","redis")
redis_client.set("age",18,60)#设置键值有效时间

#3.获取值
print(redis_client.get("name"))

is_exist=redis_client.exists("name")
print(is_exist)
redis_client.close()
