import openai
import requests
from dto.chat_dto import MessageDto


class LLMService:
    def __init__(self, api_key: str, folder_id: str, api_host: str, temperature: float):
        self.api_key = api_key
        self.folder_id = folder_id
        self.temperature = temperature

        self.client = openai.OpenAI(
            api_key=self.api_key,
            base_url=api_host
        )
        self.api_url = api_host

        if 'v1/completion' not in self.api_url:
            self.api_url = 'https://llm.api.cloud.yandex.net/foundationModels/v1/completion'

    def get_completion(self, system_prompt: str, messages: list[MessageDto]) -> str:
        formatted_messages = []

        if system_prompt:
            formatted_messages.append({'role': 'system', 'text': system_prompt})

        for msg in messages:
            if msg.content and msg.content.strip():
                formatted_messages.append({'role': msg.role, 'text': msg.content})

        if not formatted_messages:
            return 'Пустой запрос, нечего отправлять.'

        payload = {
            'modelUri': f'gpt://{self.folder_id}/yandexgpt-lite',
            'completionOptions': {
                'stream': False,
                'temperature': self.temperature,
                'maxTokens': '2000'
            },
            'messages': formatted_messages
        }

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Api-Key {self.api_key}'
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=payload) # type: ignore
            if response.status_code != 200:
                raise Exception(f'Ошибка API: {response.status_code} - {response.text}')
            result = response.json()

            return result['result']['alternatives'][0]['message']['text']

        except Exception as e:
            print(f'Проблема с API: {e}')
            raise
