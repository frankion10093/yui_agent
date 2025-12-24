import asyncio
import aiohttp

async def fetch_url(url, name):
    # async with aiohttp.ClientSession() as session:
    #     # aiohttp的get请求是可等待对象，会自动让出执行权（等待网络响应时，事件循环去执行其他任务）
    #     async with session.get(url) as response:
    #         print(f"{name} 请求返回状态码：{response.status}")
    #         return await response.text()
    a = aiohttp.ClientSession()
    res = await a.post(url)
    print(res.text())
    await a.close()
async def test2():
    while True:
        print("2222")

async def main():
    # 方式1：创建任务并等待所有任务完成
    task1 = asyncio.create_task(test1())
    task2 = asyncio.create_task(test2())
    await asyncio.gather(task1, task2)  # 等待两个任务并发执行

    # 方式2：等价写法（更简洁）
    # await asyncio.gather(test1(), test2())

# 只调用一次asyncio.run，运行主协程
asyncio.run(main())