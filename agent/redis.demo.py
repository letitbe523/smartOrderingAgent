def redis_command_demo1():
    """
    redis相关的命令demo演示
    """

    from redis import Redis

    # 1、获取到client对象
    client = Redis.from_url('redis://localhost:6379',decode_responses=True)

    # 2、通过client对象执行命令
        # 命令很多，可以将命令做一些分类(value)：
            #字符串相关的命令
            #hash map相关的命令
            #list相关的命令
            #set相关的命令
            #zset相关的命令


    # 2.1 字符串相关的命令：执行set命令，创建一个value类型为string的键值对
    client.set('name', '张三')

    # 执行get命令，获取键为name的值

    name = client.get('name')
    print(name)

    # 2.2 hash map相关的命令：创建一个value类型为hash map 的键值对
    client.hset('faq:items:address:test',mapping={'question': '地址是多少？', 'answer': '河南电子科技大学龙湖校区南苑餐厅3楼'})

    # 获取某一个key所对应的hash map
    faq_item = client.hgetall('faq:items:address:test')

    print(faq_item)

    # 2.3 set相关的命令：value为一个集合的键值对
    # 添加了一个 key = faq:items value ={'address','phone','email'}的一个key-value对
    client.sadd("faq:items","address","phone","email")
    # result 就是key=faq:items 对应的value集合
    result = client.smembers("faq:items")
    print("添加后的集合：", result)

    # 删除集合中的元素：使用 srem 命令
    client.srem("faq:items", "phone", "email", "address")
    # 再次查看集合
    result_after_delete = client.smembers("faq:items")
    print("删除后的集合：", result_after_delete)

def redis_command_demo2():
    """
    redis的pipline命令的演示：
    """

    from redis import Redis

    # 1、获取到client对象
    client = Redis.from_url('redis://localhost:6379',decode_responses=True)

    # 2、通过client，获取到pipeline对象
    pipeline = client.pipeline()

    # 3、使用pipeline声明，需要执行的命令,这个时候还没有进行通信，只是将命令放入到pipeline中
    pipeline.set('name', '张三')

    pipeline.get('name')

    pipeline.hset('faq:items:phone:test',mapping={'question': '手机号是多少？', 'answer': '131985211'})

    # 4、执行pipeline中的命令，这个时候和serve进行通信，执行命令
    results = pipeline.execute()

    print(results)



redis_command_demo1()