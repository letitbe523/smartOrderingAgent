"""
用来定义agent的函数
"""

from sqlalchemy import text

from langchain.tools import tool
import pymysql
import os

#这个dotenv是用来加载环境变量的库，可以从.env文件中加载环境变量，或者直接从操作系统的环境变量中加载，这样就不需要在代码中硬编码数据库的连接信息了，更安全也更灵活
from dotenv import load_dotenv
load_dotenv()

"""
这个DictCursor是pymysql提供的一个游标类，可以让我们以字典的形式获取查询结果，这样就可以通过键来访问查询结果中的字段了，
更方便一些，没有这个的话，查询结果是一个元组，我们就需要通过索引来访问字段了，不太直观。有这个的话，返回的查询结果就是一个列表，
列表中的每个元素都是一个字典，字典的键就是数据库表中的字段名，值就是对应的字段值了，这样我们就可以通过键来访问查询结果中的字段了，更方便一些。
"""
from pymysql.cursors import DictCursor

from pathlib import Path
#本文件两次父目录，直接到smartorderingagent的根目录
root_path = Path(__file__).parent.parent

embeddings = None
milvus_client = None

#mysql连接池
engine = None
agent = None

#这个函数用来获取embeddings的实例了，采用了单例模式了，这样就可以避免重复创建embeddings实例了，节省资源了，只有在第一次调用这个函数的时候才会创建embeddings实例了，以后的调用都会直接返回已经创建好的实例了，这样就能更高效地使用embeddings了
def get_embeddings():
    global embeddings
    if embeddings is None:
        from langchain_huggingface import HuggingFaceEmbeddings
        embeddings = HuggingFaceEmbeddings(model = str(root_path/"models"/"bge-m3"))
    return embeddings

def get_milvus_client():
    global milvus_client
    if milvus_client is None:
        import pymilvus
        milvus_client = pymilvus.MilvusClient(uri = os.getenv("MILVUS_URI"),token = os.getenv("MILVUS_TOKEN"))
    return milvus_client


def mysql_connection():
    global engine
    if engine is None:
        from sqlalchemy import create_engine
        engine = create_engine(
            url = f"mysql+pymysql://{os.getenv('MYSQL_USERNAME')}:{os.getenv('MYSQL_PASSWORD')}@{os.getenv('MYSQL_HOST')}:{os.getenv('MYSQL_PORT')}/{os.getenv('MYSQL_DATABASE')}",
            pool_size = 15              
            )
    return engine

#这个函数已经变成agent调用的工具了
@tool
def search_main_dishes():

    """
    用来搜索餐厅当中的的主菜
    """

    #用这个@tool装饰器的函数必须有文档字符串，在agent调用这个工具的时候会显示这个描述信息，是必不可少的，就是docstring了，不能没有的，不然agent就不知道这个工具是干什么的了，这个描述信息要写清楚，最好能包含这个工具的功能、输入输出、使用场景等信息，这样agent在调用这个工具的时候就能更好地理解这个工具的作用了，也能更好地选择什么时候调用这个工具了

    #把数据库表中的字段名映射成中文，这样在返回结果的时候可以中文显示，这个映射关系可以根据实际情况来调整的，主要是为了让返回的结果更符合用户的习惯和理解了
    key_name_mapping = {
        "dish_name": "主菜名称",
        "price": "价格",
        "description": "描述",
        "category": "类别",
        "spice_level": "辣度等级",
        "flavor": "口味",
        "main_ingredients": "主要食材",
        "cooking_method": "烹饪方法",
        "is_vegetarian": "是否素食",
        "allergens": "过敏原"
    }


    """
    把那个menu.sql导入navicat里面的数据库menu，就能通过查找数据库来获取主菜的相关信息
    查数据库用pymysql，连接数据库，执行查询语句，获取主菜的信息，做过开发的都知道.
    不要通过硬编码的方式，要用环境变量来获取数据库的连接信息，这样更安全，也更灵活，环境变量可以通过在项目根目录下创建一个.env文件来设置，或者直接在操作系统的环境变量中设置
    """
    with pymysql.connect(host=os.getenv("MYSQL_HOST"), port=int(os.getenv("MYSQL_PORT")), user=os.getenv("MYSQL_USERNAME"), password=os.getenv("MYSQL_PASSWORD"), database="menu") as connection:
        #这个cursor是一个对象，提供了执行SQL语句的方法，这里我们用它来执行一个查询主菜的SQL语句
        #dictcursor还能传入字段，可以看到查询结果的字段名了，不用通过索引来访问了，更方便一些
        with connection.cursor(DictCursor) as cursor:
            sql = """
                select 
                    dish_name,
                    price,
                    description,
                    category,
                    spice_level,
                    flavor,
                     main_ingredients,
                    cooking_method,
                    is_vegetarian,
                    allergens
                from
                    menu.menu_items
                where
                    is_featured = 1
            """
    
            cursor.execute(sql)
            results = cursor.fetchall()
    
            #返回选菜结果
            #return results

            #定义json的键，将数据封装成json格式返回
            json_results = []
            #item就是每一条数据
            for item in results:
                json_item = {}
                #获取字典中的键和值，key就是数据库表中的字段名，value就是对应的字段值
                for key, value in item.items():
                    #把数据库表中的字段名映射成中文
                    json_item[key_name_mapping[key]] = value
                json_results.append(json_item)

            return json_results

@tool
def user_flavor_search(user_query: str):

    """
    基于用户的口味，来去查找相关的菜品
    """

    """这个时候不能用关系型数据库了，因为用户的口味是一个比较模糊的概念，关系型数据库不太适合存储和查询这种非结构化的数据了，
    这个时候可以考虑用向量数据库来存储菜品的信息，然后通过计算用户查询和菜品信息的相似度来进行搜索了，这样就能更好地满足用户的需求了
    """
    #这个pymilvus是milvus提供的一个Python客户端库，可以用来连接和操作milvus数据库了，milvus是一个开源的向量数据库，专门用来存储和查询向量数据的，适合存储和查询这种非结构化的数据了，比如文本、图片、音频等了，这个库提供了很多方法可以用来创建集合、插入数据、查询数据等了，我们可以用它来把菜品的信息存储在milvus中，然后通过计算用户查询和菜品信息的相似度来进行搜索了
    import pymilvus
    #这个huggingfaceembeddings是用来把文本转换成向量的库，这个库提供了很多预训练的模型可以用来生成文本的向量表示了，这样我们就可以把菜品的信息转换成向量存储在milvus中，然后通过计算用户查询和菜品信息的相似度来进行搜索了
    from langchain_huggingface import HuggingFaceEmbeddings

    #1、构建用户query的向量
    embeddings = get_embeddings()

    #这个函数可以把用户的查询转换成一个向量了，这个向量就是一个高维的数值表示了，包含了用户查询的语义信息了，这样我们就可以通过计算这个向量和菜品信息的向量之间的相似度来进行搜索了
    #采用稠密向量，不用稀疏向量了，稠密向量是一个连续的数值表示了，包含了更多的语义信息了，稀疏向量是一个离散的数值表示了，包含的信息比较有限了，稠密向量更适合用来存储和查询这种非结构化的数据了，比如文本、图片、音频等了
    query_vector = embeddings.embed_query(user_query)

    #2、连接milvus,进行向量搜索,这个时候就需要在milvus中预先存储好菜品的信息了，存储的时候也要把菜品的信息转换成向量存储在milvus中，这样我们就可以通过计算用户查询的向量和菜品信息的向量之间的相似度来进行搜索了，这个相似度可以通过余弦相似度、欧氏距离等方法来计算了，milvus提供了很多方法可以用来计算相似度了，我们可以根据实际情况来选择合适的方法了
    client = get_milvus_client()

    #3、进行向量搜索
    search_res = client.search(
        collection_name = "menu_items",
        data=[query_vector],
        anns_field="vector",
        output_fields=["text"],
        limit=1
        )
    
    #4、解析搜索结果
    if search_res:
        #就是取search_res中的data字段
        all_results = search_res[0]
        #这个时候all_results就是一个列表了，列表中的每个元素都是一个搜索结果了，每个搜索结果都是一个字典了，字典中包含了菜品的信息了
        final_results = []

        for item in all_results:
            item_str = item["entity"]['text']
            final_results.append(item_str)

        return final_results
    else:
        return "在当前库里面没有找到和用户喜好相关的菜品"


from pydantic import BaseModel, Field

class ReservationToolArgsInfo(BaseModel):
    num_people: int = Field(description="预约的人数")
    num_children: int = Field(description="预约的0-2岁儿童人数")
    arrival_time: str = Field(description="预约的到达时间,格式:YYYY-MM-DD HH:MM:SS")
    seat_preference: str = Field(description="预约的座位偏好,当用户没有特殊需求时,传递空字符串即可")
    main_dish_preference: str = Field(description="预订的主菜偏好,当用户没有特殊需求时,传递空字符串即可")
    comment: str = Field(description="预约的其他备注,当用户没有特殊需求时,传递空字符串即可")

@tool(args_schema=ReservationToolArgsInfo)
def make_reservation(num_people:int, num_children:int, arrival_time:str, seat_preference:str, main_dish_preference:str, comment:str):

    """
    用来进行餐厅预定的工具
    通过MySQL向数据库当中写入数据,所有数据库的连接，都是从连接池取出来的，所以不需要每次都创建连接了，只需要创建连接池，
    然后从连接池中取连接就可以了，这样就可以避免每次都创建连接和关闭连接了，可以提升性能了
    """
    engine = mysql_connection()
    #values不能用%s，因为%s是字符串占位符，不能用来插入数值，应该用:来占位，然后通过parameters来传递参数
    with engine.connect() as conn:
        sql = """
            insert into reservation_order(num_people, num_children, arrival_time, seat_preference, main_dish_preference, other_comments)
            values (:num_people, :num_children, :arrival_time, :seat_preference, :main_dish_preference, :other_comments)
        """

        params = {
            "num_people": num_people,
            "num_children": num_children,
            "arrival_time": arrival_time,
            "seat_preference": seat_preference,
            "main_dish_preference": main_dish_preference,
            "other_comments": comment
        }
        conn.execute(statement=text(sql), parameters=params)

        conn.commit()

        return "预订成功"

#流式输出，通过yield来实现的
async def assistant_query(user_query:str):
    """
    接收来自前端的用户query，然后调用agent来处理这个query，并返回结果"""
    agent = await create_agent()
    # 1、调用前，新添加一个system prompt,让agent感知当前的时间
    from datetime import datetime
    from langchain.messages import ToolMessage

    current_date = datetime.now().strftime("%Y-%m-%d")
    
    day_of_week = datetime.now().weekday() + 1
    time_system_prompt = {"role":"system","content":f"当前日期为：{current_date}，当前是周{day_of_week}"}

    # 2、config怎么去构建：config代表一次短期对话，在实际生产环境下，每个用户的每一次会话，在后端系统当中，都会有一次session_id,可以拿这个session_id作为thread_id传进去
    # 本系统简单，就给了一个固定的id，单用户；多用户就用session_id
    config = {"configurable":{"thread_id":"123"}}
    # res = await agent.ainvoke({"messages":[time_system_prompt,{"role":"user","content":user_query}]},config=config)

    #3、如何去调用agent:希望是流式输出,这样就可以实时看到agent的输出结果了，而不是等到agent处理完所有内容，再一次性返回结果了
    #异步迭代，用的是async,astream，不再是invoke了，invoke是同步的，astream是异步的，可以实时输出结果了
    async for chunk in agent.astream({"messages":[time_system_prompt,{"role":"user","content":user_query}]},config=config,stream_mode="messages"):
        #chunk首先一个tuple(元组),元组中第一个元素是(AIMessageChunk/ToolMessage,_)，第二个元素没有关心
        message = chunk[0]
        #这个message需要通过什么方式，给到谁:需要通过接口的方式给到前端，然后让前端去展示
        #SSE:Server-Sent Events,服务器发送事件，是一种允许服务器向客户端推送数据的技术，可以用来实现实时更新，比如聊天室、股票行情、新闻推送等
        #SSE是一种基于HTTP协议的技术，服务器通过HTTP响应头中的Content-Type字段来告诉浏览器，这是一个SSE响应，浏览器会自动解析这个响应，并实时接收服务器发送的数据
        #SSE的数据结构：data：{"type":"token","content":"你好"}\n\n，type表示数据类型，content表示数据内容
        
        if type(message) == ToolMessage:
            continue 


        #快速地将这个方法产出的token,给出后端接口，让后端接口去输出给前端
        import json
        #现在payload还是一个字典，需要转换成json字符串
        payload = {"content":message.content,"type":"token"}
        payload_str = json.dumps(payload,ensure_ascii=False)
        #yield好处：可以实时输出结果，不需要等到所有结果都处理完，再一次性输出，把数据打出去，main里面的接口来接收
        yield f'data: {payload_str}\n\n'




async def create_agent():
    global agent
    if agent is None:
        from langchain.agents import create_agent
        from langchain_openai import ChatOpenAI
        from langchain_mcp_adapters.client import MultiServerMCPClient
        from langgraph.checkpoint.memory import InMemorySaver

        checkpointer = InMemorySaver()

        #创建一个多服务MCP客户端，用来连接到多个MCP服务，这个客户端可以同时连接到多个MCP服务，然后通过这个客户端来调用多个MCP服务了
        client  = MultiServerMCPClient(
                connections={
                    "amap_map":{
                "transport": "sse",
                "url": "https://mcp.api-inference.modelscope.net/ccaef2a2308042/sse"
                }

                }
            )


        #创建一个语言模型实例，指定小米的模型名称
        llm = ChatOpenAI(model="mimo-v2.5-pro")

        #打开系统提示词文件，读取内容
        with open(str(root_path / "agent" / "prompts" / "system_prompt.txt"),encoding="utf-8",mode="r") as f:
            system_prompt = f.read()
        
        mcp_tools = await client.get_tools()

        #创建一个agent实例，传入语言模型、系统提示词和工具列表
        agent = create_agent(
            model=llm,
            system_prompt=system_prompt,
            tools=[search_main_dishes, user_flavor_search, make_reservation]+mcp_tools,
            checkpointer=checkpointer
        )
    return agent

#测试    
async def test_agent():
    agent = await create_agent()
    config = {"configurable":{"thread_id":"123"}}
    res = await agent.ainvoke({"messages":[{"role":"user","content":"我喜欢吃辣，可以帮我推荐几个菜吗？"}]},config=config)

    print(res["messages"][-1].content)


#测试入口，.invoke的方式调用工具函数，看看能不能正确获取主菜的信息,这个工具没有参数，所以传入一个空字典
if __name__ == "__main__":
    """    
    res = search_main_dishes.invoke({})
    print(res)"""

    """    
    res = user_flavor_search.invoke({"user_query": "有没有清淡点的菜品"})
    print(res)"""

    """    
    res = make_reservation.invoke({"num_people": 2, "num_children": 1, "arrival_time": "2026-6-5 12:00:00", "seat_preference": "", "main_dish_preference": "", "comment": ""})
    print(res)"""
    
    import asyncio
    asyncio.run(test_agent())