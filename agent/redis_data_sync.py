"""
将FAQ数据导入到Redis中,方便后续的检索
"""

FAQ_ITEMS = [

    {
        "id":"address",
        "question":"地址是什么",
        "answer":"河南电子科技大学（龙湖校区）南苑餐厅三楼"
    },
    {   
        "id":"phone",
        "question":"大堂电话是什么",
        "answer":"010-66666666,欢迎您联系"
    },
    {
        "id":"work_time",
        "question":"营业时间是什么时候",
        "answer":"我们的营业时间是：周日至周四：早10点至晚21点，周五周六：早10点至晚23点。欢迎您来哦🙂"
    }

]

def sync_faq_items_to_redis():
    """
    将FAQ_ITEMS中的数据导入到Redis中
    """
    
    # 1、获取到client和Pipeline对象
    from redis import Redis
    client = Redis.from_url('redis://localhost:6379',decode_responses=True)
    pipline = client.pipeline()

    # 2、使用pipline，将所有数据，批量写入到Redis的 hash map 中，以及将所有的key,添加到一个set中

        # 备注：当前项目比较简单，实现一个FAQ V1.0的版本：全量比对
        # 3、全量比对：当用户Query来了之后，需要把所有的faq questions都从redis里面读取出来，
        # 然后和用户的query去做一个相似度的计算，取出相似度最高的top_k个问题

        # 后面如何从redis中得知，我们有哪些key呢？
            # 方式一：redis给我们提供了一个命令：keys pattern(类似于正则匹配的一个表达式)，可以通过在这个命令获取到redis中有哪些faq的键
                # 这种方式不能用：keys命令会服务端的压力很大，占用很多资源
            # 方式二：单独创建一个set,来存储所有的faq和key
            # 每次新增一个faq item的时候，就往这个set中添加一个元素。当前，我们就使用这种方式



    """    # faq:items:address, faq:items:phone, faq:items:time
    #all_faq_keys = client.keys('faq:items:*')

    all_faq_keys = client.smembers('faq:items')
    user_query = "xxxx"
    for faq_item in all_faq_keys:
        pipline.hgetall(faq_item)

    all_faq_items = pipline.execute()

    scores = []
    for faq_item in all_faq_items:
        
        scores.append(_get_similarity_score(user_query,faq_item['question']))

    #最后从scores里面取出top_k个元素，所对应的question,然后展示在前端"""

    keys_list = []
    for faq_item in FAQ_ITEMS:

        #1、将数据写入到hash map中
        key = f"faq:items:{faq_item['id']}"
        pipline.hset(
            name = key,
            mapping = {
                "question":faq_item['question'],
                "answer":faq_item['answer']
            }

        )

        #2、将它的key添加到faq:items这个set中,速度会好一些
        #pipline.sadd('faq:items',key)
        keys_list.append(key)

    pipline.sadd('faq:all_items',*keys_list)
    #3、执行pipline.execute
    result = pipline.execute()
    all_faq_keys = client.smembers('faq:all_items')
    print(all_faq_keys)



#def _get_similarity_score(user_query:str,faq_question:str)-> float:

#现在已经把数据同步到redis里面了
if __name__ == "__main__":
    sync_faq_items_to_redis()