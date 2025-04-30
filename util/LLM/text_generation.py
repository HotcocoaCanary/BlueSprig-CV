import uuid

import requests

from util.LLM.aigc_auth import gen_sign_headers

"""
文本生成
"""


class TextGeneration:
    def __init__(self):
        self.domain = 'api-ai.vivo.com.cn'
        self.uri = '/vivogpt/completions'
        self.method = 'POST'

    def blue_llm_70B(self, messages, system_prompt="", temperature=0.9):
        params = {
            'requestId': str(uuid.uuid4())
        }
        data = {
            'messages': messages,
            'model': 'vivo-BlueLM-TB-Pro',
            'sessionId': str(uuid.uuid4()),
            'extra': {
                'temperature': temperature
            },
            'systemPrompt': system_prompt
        }
        headers = gen_sign_headers(self.method, self.uri, params)
        headers['Content-Type'] = 'application/json'

        url = f'https://{self.domain}{self.uri}'
        response = requests.post(url, json=data, headers=headers, params=params)

        if response.status_code == 200:
            res_obj = response.json()
            if res_obj['code'] == 0 and 'data' in res_obj:
                return res_obj['data']['content']
            else:
                return f"Error: {res_obj['msg']}"
        else:
            return f"HTTP Error: {response.status_code} {response.text}"

    def blue_llm_multimodal(self, message, temperature=0.9):
        params = {
            'requestId': str(uuid.uuid4())
        }
        data = {
            'sessionId': str(uuid.uuid4()),
            'requestId': params['requestId'],
            'model': 'vivo-BlueLM-V-2.0',
            "messages": message,
            'extra': {
                'temperature': temperature
            }
        }
        headers = gen_sign_headers(self.method, self.uri, params)
        headers['Content-Type'] = 'application/json'

        url = f'https://{self.domain}{self.uri}'
        response = requests.post(url, json=data, headers=headers, params=params)

        if response.status_code == 200:
            res_obj = response.json()
            if res_obj['code'] == 0 and 'data' in res_obj:
                return res_obj['data']['content']
            else:
                return f"Error: {res_obj['msg']}"
        else:
            return f"HTTP Error: {response.status_code} {response.text}"
