import os.path

from llm import get_agent
from funasr import AutoModel

import speech_recognition as sr
from .ai_tts import tts
from thread_pool_manager import get_thread_pool_manager
from message import get_message_manager


message_manager = get_message_manager()


thread_pool_manager = get_thread_pool_manager()

agent = get_agent()

path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "ai_model"
)


print(path)

model = model = AutoModel(model="paraformer-zh", model_revision="v2.0.4",
                  vad_model="fsmn-vad", vad_model_revision="v2.0.4",
                  punc_model="ct-punc-c", punc_model_revision="v2.0.4",
                  # spk_model="cam++", spk_model_revision="v2.0.2",
                  )

r = sr.Recognizer()
r.pause_threshold = 3

def asr():
    while True:
        try:

            # 如果检测到人声，开始录音，采样率为16000，60秒内没有人声会抛出错误
            print("开始录音")
            with sr.Microphone(sample_rate=16000) as source:
                r.adjust_for_ambient_noise(source, duration=1)
                audio = r.listen(source, timeout=60)

            print("录音结束")

            wav_bite = audio.get_raw_data(convert_rate=16000, convert_width=2)

            res = model.generate(input=wav_bite, batch_size_s=300,show_progress_bar=False,)[0]['text']

            print(res)

            if res.strip() != '':
                tts(agent.chat(res))

        except Exception as e:
            print(e)


if __name__ == "__main__":
    asr()
