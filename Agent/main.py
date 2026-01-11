from thread_pool_manager import get_thread_pool_manager
from config import core_config
from llm import get_agent
from ai_voice import asr,tts
import keyboard
from message import get_message_manager

message_manager = get_message_manager()

agent = get_agent()

thread_pool_manager = get_thread_pool_manager()


if __name__ == '__main__':
    if core_config.isOpenTTs:
        thread_pool_manager.submit_front_executor("asr",asr)

    while True:
        if keyboard.is_pressed('q'):
            break

        user_input = input("用户输入:")
        message_manager.add_local_message(user_input)

        tts(agent.chat(user_input))





