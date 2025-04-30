import base64
import json
import os
import time
import wave
from datetime import datetime
from urllib.parse import urlencode
from typing import Optional
from websocket import WebSocket, create_connection, ABNF

from util.LLM.aigc_auth import gen_sign_headers
from dotenv import load_dotenv

load_dotenv()
"""
文本转语音 
"""


class TTSConnectionError(Exception):
    """自定义连接异常"""
    pass


class TTSSynthesisError(Exception):
    """自定义合成异常"""
    pass


class TTSValidationError(ValueError):
    """参数验证异常"""
    pass


class TTS:
    """Vivo语音合成优化版"""

    _ENGINE_VOICES = {
        'short_audio_synthesis_jovi': {
            'vivoHelper', 'yunye', 'wanqing', 'xiaofu',
            'yige_child', 'yige', 'yiyi', 'xiaoming'
        },
        'long_audio_synthesis_screen': {
            'x2_vivoHelper', 'x2_yige', 'x2_yige_news', 'x2_yunye',
            'x2_yunye_news', 'x2_M02', 'x2_M05', 'x2_M10', 'x2_F163',
            'x2_F25', 'x2_F22', 'x2_F82'
        },
        'tts_humanoid_lam': {
            'F245_natural', 'M24', 'M193', 'GAME_GIR_YG',
            'GAME_GIR_MB', 'GAME_GIR_YJ', 'GAME_GIR_LTY', 'YIGEXIAOV',
            'FY_CANTONESE', 'FY_SICHUANHUA', 'FY_MIAOYU'
        }
    }

    def __init__(self, output_dir: Optional[str] = None):
        """
        初始化TTS实例
        :param output_dir: 音频输出目录，默认读取环境变量AUDIO_PATH
        """
        self.output_dir = output_dir or os.getenv("AUDIO_PATH", "./audio_output")
        os.makedirs(self.output_dir, exist_ok=True)
        self._ws: Optional[WebSocket] = None

    def generate_audio(
            self,
            engineid: str,
            vcn: str,
            text: str,
            speed: int = 50,
            volume: int = 50
    ) -> str:
        """
        生成语音文件
        :param engineid: 引擎类型
        :param vcn: 发音人
        :param text: 合成文本
        :param speed: 语速 (0-100)
        :param volume: 音量 (1-100)
        :return: 生成的音频文件路径
        """
        try:
            self._validate_params(engineid, vcn, speed, volume)
            self._connect(engineid)
            audio_data = self._synthesize(vcn, text, speed, volume)
            return self._save_audio(engineid, vcn, audio_data)
        except Exception as e:
            self._close_connection()
            raise e

    def _validate_params(
            self,
            engineid: str,
            vcn: str,
            speed: int,
            volume: int
    ) -> None:
        """参数验证"""
        if engineid not in self._ENGINE_VOICES:
            raise TTSValidationError(
                f"Invalid engineid: {engineid}. "
                f"Valid options: {list(self._ENGINE_VOICES.keys())}"
            )

        if vcn not in self._ENGINE_VOICES[engineid]:
            raise TTSValidationError(
                f"Voice {vcn} not supported for {engineid}. "
                f"Valid voices: {self._ENGINE_VOICES[engineid]}"
            )

        if not 0 <= speed <= 100:
            raise TTSValidationError("Speed must be between 0-100")

        if not 1 <= volume <= 100:
            raise TTSValidationError("Volume must be between 1-100")

    def _connect(self, engineid: str) -> None:
        """建立WebSocket连接"""
        try:
            params = {
                'engineid': engineid,
                'system_time': str(int(time.time())),
                'user_id': 'tts_service',
                'model': 'unknown',
                'product': 'unknown',
                'package': 'unknown',
                'client_version': '1.0',
                'system_version': 'unknown',
                'sdk_version': '1.0',
                'android_version': 'unknown'
            }

            headers = gen_sign_headers('GET', '/tts', params)
            url = f"wss://api-ai.vivo.com.cn/tts?{urlencode(params)}"

            self._ws = create_connection(url, header=headers)
            self._validate_handshake()

        except Exception as e:
            raise TTSConnectionError(f"Connection failed: {str(e)}")

    def _validate_handshake(self) -> None:
        """验证握手响应"""
        if not self._ws:
            return

        code, data = self._ws.recv_data()
        try:
            resp = json.loads(data)
            if resp.get('error_code') != 0:
                raise TTSConnectionError(f"Handshake failed: {resp.get('error_msg')}")
        except json.JSONDecodeError:
            raise TTSConnectionError("Invalid handshake response format")

    def _synthesize(
            self,
            vcn: str,
            text: str,
            speed: int,
            volume: int
    ) -> bytes:
        """执行合成流程"""
        if not self._ws:
            raise TTSConnectionError("Not connected to TTS service")

        payload = {
            "aue": 0,
            "auf": "audio/L16;rate=24000",
            "vcn": vcn,
            "speed": speed,
            "volume": volume,
            "text": base64.b64encode(text.encode()).decode(),
            "encoding": "utf8",
            "reqId": int(time.time() * 1000)
        }

        self._ws.send(json.dumps(payload))
        return self._receive_audio_data()

    def _receive_audio_data(self) -> bytes:
        """接收音频数据"""
        audio_data = b''
        try:
            while True:
                code, data = self._ws.recv_data()
                if code == ABNF.OPCODE_TEXT:
                    resp = json.loads(data)
                    if resp['error_code'] != 0:
                        raise TTSSynthesisError(resp['error_msg'])

                    audio_data += base64.b64decode(resp['data']['audio'])
                    if resp['data']['status'] == 2:
                        break
        except (ConnectionResetError, TimeoutError) as e:
            raise TTSSynthesisError(f"Connection interrupted: {str(e)}")

        return audio_data

    def _save_audio(
            self,
            engineid: str,
            vcn: str,
            pcm_data: bytes
    ) -> str:
        """保存音频文件"""
        filename = (
            f"{engineid}_{vcn}_"
            f"{datetime.now().strftime('%Y%m%d%H%M%S')}.wav"
        )
        output_path = os.path.join(self.output_dir, filename)

        try:
            with wave.open(output_path, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(24000)
                wav_file.writeframes(pcm_data)
            return output_path
        except Exception as e:
            raise IOError(f"Failed to save audio: {str(e)}")

    def _close_connection(self) -> None:
        """安全关闭连接"""
        if self._ws:
            try:
                self._ws.close()
            except Exception:
                pass
            finally:
                self._ws = None

    def __del__(self):
        """析构函数确保连接关闭"""
        self._close_connection()