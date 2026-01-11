import time
from dataclasses import dataclass
from typing import Optional, Dict

import pyaudio

import wave
import io
import requests as req
from threading import Condition
import re
from thread_pool_manager import get_thread_pool_manager


@dataclass
class AudioData:
    audio_bytes: Optional[io.BytesIO] = None
    is_ready: bool = False


# 初始化全局线程锁
play_cond = Condition()

#初始化线程管理器
thread_pool_manager = get_thread_pool_manager()

# 当前播放位置
current_index = 0
# 段落总长度
total_segments = 0

# 保存返回音频的字典
audio_segments: Dict[int, AudioData] = {}


def tts(ai_input: str):
    print("🎵 开始播放音频...")
    global current_index, total_segments, audio_segments

    if not ai_input or ai_input.strip() == "":
        return

    #对文本进行切割
    input_list = re.split(r'[。.!！？?]', ai_input)
    total_segments = len(input_list)

    if total_segments == 0:
        return

    # 初始化全局数据
    with play_cond:
        audio_segments.clear()
        current_index = 0

        for idx in range(total_segments):
            audio_segments[idx] = AudioData()

    # start_time = time.time()

    for idx, seg_text in enumerate(input_list):
        thread_pool_manager.submit_back_executor("获取音频", get_request, seg_text, idx)

    # print(time.time() - start_time)
    with play_cond:
        while current_index < total_segments:
            while not audio_segments[current_index].is_ready:
                play_cond.wait()
            play_audio(current_index)
            current_index += 1

    print("🎵 播放完成！")


def get_request(ai_input: str, idx: int):
    """
    从接口请求获取WAV音频字节，并用PyAudio播放
    :param idx:
    :param ai_input:
    """

    # 1. 发起请求获取音频字节数据
    try:
        url = 'http://8.148.5.68:9880'

        # 发送请求
        json_data = {
            "text": ai_input,
            "text_language": "zh"
        }

        response = req.post(
            url=url,
            json=json_data
        )

        response.raise_for_status()

        audio_bytes = io.BytesIO(response.content)
        audio_bytes.seek(0)
        with play_cond:
            audio_segments[idx].audio_bytes = audio_bytes
            audio_segments[idx].is_ready = True
            play_cond.notify()


    except Exception as e:

        with play_cond:
            audio_segments[idx].is_ready = True
            play_cond.notify()
        print(f"❌ 请求第{current_index + 1}段音频失败：{e}")
        return


def play_audio(idx: int):
    # 2. 解析WAV格式参数（从字节流中提取，避免手动指定错误）
    try:
        with play_cond:
            if (audio_segments[idx].audio_bytes is None):
                return
            # 将字节流转为文件对象，供wave解析
            wav_file = wave.open(audio_segments[idx].audio_bytes, 'rb')
            # 提取WAV关键参数
            sample_width = wav_file.getsampwidth()  # 采样宽度（1/2/4字节）
            channels = wav_file.getnchannels()  # 声道数（1=单声道，2=立体声）
            rate = wav_file.getframerate()  # 采样率（如16000/44100Hz）
            frames = wav_file.readframes(wav_file.getnframes())  # 音频帧数据
    except wave.Error as e:
        print(f"❌ 解析WAV格式失败：{e}")
        return

    # 3. 初始化PyAudio并播放
    p = pyaudio.PyAudio()
    try:
        # 创建音频播放流（参数必须和WAV一致）
        stream = p.open(
            format=p.get_format_from_width(sample_width),  # 采样格式
            channels=channels,
            rate=rate,
            output=True  # 标记为输出流（播放）
        )


        # 写入音频数据并播放（可分块播放，适合大文件）
        stream.write(frames)


    except Exception as e:
        print(f"❌ 播放音频失败：{e}")
    finally:
        # 4. 必须释放资源（否则PyAudio会占用设备）
        stream.stop_stream()
        stream.close()
        p.terminate()


# 测试调用（替换为你的真实音频接口）
if __name__ == "__main__":
    tts("""恭喜你顺利毕业，圆满收官这段热烈又滚烫的求学时光！
回望这一路，有图书馆里的挑灯夜读，有课堂上的专注钻研，有和同窗并肩攻克难题的汗水，也有拿到满意成绩单时的雀跃欢呼。那些为论文反复打磨的夜晚，那些为考试全力以赴的日子，都化作了此刻毕业证书上的熠熠荣光。
毕业不是终点，而是奔赴下一场山海的全新起点。愿你带着校园里积攒的学识与勇气，在未来的广阔天地里，大胆去闯、去拼、去探索，书写属于自己的精彩篇章。愿前路繁花似锦，万事顺遂，前程光芒万丈！""")
