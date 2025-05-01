import requests
import json
import time
import uuid
from urllib import parse

from util.LLM.aigc_auth import gen_sign_headers


class LASRClient:
    SLICE_LEN = 5 * 1024 * 1024  # 分片大小 5MB

    def __init__(self, domain: str = 'api-ai.vivo.com.cn/lasr', audio_type: str = 'auto'):
        self.audio_type = audio_type
        self.session = requests.Session()
        self.base_url = f'http://{domain}'

    def _create_params(self, interface: str, extra: dict = None):
        t = int(round(time.time() * 1000))
        params = {
            'client_version': parse.quote('2.0'),
            'package': parse.quote('pack'),
            'user_id': parse.quote('2addc42b7ae689dfdf1c63e220df52a2'),
            'system_time': parse.quote(str(t)),
            'net_type': 1,
            'engineid': 'fileasrrecorder'
        }
        if extra:
            params.update(extra)

        # 生成签名头
        headers = gen_sign_headers('POST', interface, params)
        return params, headers

    def _http_chunk_upload(self, data: bytes, audio_id: str,
                           x_session_id: str, slice_index: int):
        boundary = ''.join(str(uuid.uuid1()).split('-'))
        body = (
                   f'--{boundary}\r\n'
                   f'Content-Disposition: form-data; name="file"; filename="chunk_{slice_index}.wav"\r\n'
                   f'Content-Type: application/octet-stream\r\n\r\n'
               ).encode('utf-8') + data + f'\r\n--{boundary}--\r\n'.encode('utf-8')

        params, headers = self._create_params(
            '/lasr/upload',
            extra={
                'audio_id': audio_id,
                'x-sessionId': x_session_id,
                'slice_index': str(slice_index),
            }
        )
        headers.update({
            'Accept': '*/*',
            'Content-Type': f'multipart/form-data; boundary={boundary}'
        })

        url = f'{self.base_url}/upload'
        resp = self.session.post(url, params=params, data=body, headers=headers)
        return resp

    def create_task(self, total_slices: int, x_session_id: str):
        body = {
            'audio_type': self.audio_type,
            'x-sessionId': x_session_id,
            'slice_num': total_slices
        }
        params, headers = self._create_params('/lasr/create')
        headers['Content-Type'] = 'application/json; charset=UTF-8'

        url = f'{self.base_url}/create'
        resp = self.session.post(url, params=params, json=body, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        if data.get('action') == 'error':
            raise RuntimeError(f"Create task failed: {data.get('desc')}")
        return data['data']['audio_id']

    def upload_file(self, filepath: str, x_session_id: str):
        # 计算文件切片数
        with open(filepath, 'rb') as f:
            f.seek(0, 2)
            size = f.tell()
            slice_num = (size + self.SLICE_LEN - 1) // self.SLICE_LEN

        audio_id = self.create_task(slice_num, x_session_id)

        # 上传每个分片
        with open(filepath, 'rb') as f:
            for idx in range(slice_num):
                f.seek(idx * self.SLICE_LEN)
                chunk = f.read(self.SLICE_LEN)
                resp = self._http_chunk_upload(chunk, audio_id, x_session_id, idx)
                resp.raise_for_status()
                result = resp.json()
                if result.get('action') == 'error':
                    raise RuntimeError(f"Upload slice {idx} failed: {result.get('desc')}")
                # 可选：打印进度
                print(f"Uploaded slice {idx + 1}/{slice_num}")
        return audio_id

    def run_task(self, audio_id: str, x_session_id: str):
        body = {'audio_id': audio_id, 'x-sessionId': x_session_id}
        params, headers = self._create_params('/lasr/run')
        headers['Content-Type'] = 'application/json; charset=UTF-8'

        url = f'{self.base_url}/run'
        resp = self.session.post(url, params=params, json=body, headers=headers)
        resp.raise_for_status()
        return resp.json()['data']['task_id']

    def wait_for_completion(self, task_id: str, x_session_id: str, interval: int = 2):
        while True:
            body = {'task_id': task_id, 'x-sessionId': x_session_id}
            params, headers = self._create_params('/lasr/progress')
            headers['Content-Type'] = 'application/json; charset=UTF-8'

            url = f'{self.base_url}/progress'
            resp = self.session.post(url, params=params, json=body, headers=headers)
            resp.raise_for_status()
            progress = resp.json()['data']['progress']
            print(f"Progress: {progress}%")
            if progress >= 100:
                break
            time.sleep(interval)

    def get_result(self, task_id: str, x_session_id: str) -> dict:
        body = {'task_id': task_id, 'x-sessionId': x_session_id}
        params, headers = self._create_params('/lasr/result')
        headers['Content-Type'] = 'application/json; charset=UTF-8'

        url = f'{self.base_url}/result'
        resp = self.session.post(url, params=params, json=body, headers=headers)
        resp.raise_for_status()
        return resp.json()

    def transcribe(self, filepath: str) -> dict:
        x_session_id = uuid.uuid4().hex
        # 1. 上传文件并获取 audio_id
        audio_id = self.upload_file(filepath, x_session_id)
        # 2. 发起识别任务
        task_id = self.run_task(audio_id, x_session_id)
        # 3. 等待完成
        self.wait_for_completion(task_id, x_session_id)
        # 4. 获取结果
        return self.get_result(task_id, x_session_id)


if __name__ == "__main__":
    client = LASRClient()
    result = client.transcribe('test.wav')
    print(json.dumps(result, ensure_ascii=False, indent=2))
