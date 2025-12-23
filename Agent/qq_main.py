from thread_pool_manager import thread_pool_manager
from qq import qq_manager
from llm import chatbot

thread_pool_manager.submit_front_executor("获取qq消息线程", qq_manager.start_listen)

thread_pool_manager.submit_back_executor("ai回复线程", chatbot.send_message)

print("back", thread_pool_manager.get_back_task_detail())
print("front", thread_pool_manager.get_front_task_detail())

while True:
    pass
