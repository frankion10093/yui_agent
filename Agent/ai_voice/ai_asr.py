import logging
import numpy as np
import speech_recognition as sr
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks

inference_pipeline = pipeline(
        task=Tasks.auto_speech_recognition,
        model='iic/SenseVoiceSmall',
        model_revision="master",
        device="cpu", )

def ai_asr():
    logging.info("🤖 开始录音，请说话...")
    #初始化语音识别器，这个主要还是用来实现人声的识别的，并没有使用asr功能
    r = sr.Recognizer()
    r.pause_threshold = 1
    try:
        # 如果检测到人声，开始录音，采样率为16000，60秒内没有人声会抛出错误
        with sr.Microphone(sample_rate=16000) as source:
            r.adjust_for_ambient_noise(source, duration=1)
            audio = r.listen(source, timeout=60)
        #由于funasr的模型输入要求是float32，所以需要将音频数据转换为float32
        audio_data = np.frombuffer(audio.get_raw_data(), dtype=np.int16)
        # 转换为float32,为什么这里需要/ 32768.0,实际是为了达到归一化目的，int16就是2的15次方，所以除以32768.0就是归一化到[-1,1]
        audio_data = audio_data.astype(np.float32)/ 32768.0
        #这里调用funasr的模型进行语音识别，直接取[0]['text']，即返回第一个结果的文本
        # text = model.generate(input=audio_data, sample_rate=16000)[0]["text"]
        text = inference_pipeline(audio_data)[0]['text']
        logging.info(text)
        return text

    except Exception as e:
        logging.error("❌ Error:语音转文字出错！可能是模型加载出错或者输入设备问题！")
        print(e)
        return ''

if __name__ == '__main__':
    print(ai_asr())
