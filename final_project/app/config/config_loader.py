import os
import yaml
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    api_key: str
    api_host: str
    folder_id: str
    limit_message: int
    limit_chars: int
    temperature: float
    system_prompt: Optional[str]


def load_config() -> Config:
    load_dotenv()

    yaml_config: dict = {}
    if os.path.exists('config.yaml'):
        with open('config.yaml', 'r', encoding='utf-8') as f:
            yaml_config = yaml.safe_load(f) or {}

    api_key = os.getenv('YANDEX_API_KEY') or yaml_config.get('api_key')
    folder_id = os.getenv('YANDEX_FOLDER_ID') or yaml_config.get('folder_id')
    api_host = os.getenv('API_HOST') or yaml_config.get('api_host', 'https://llm.api.cloud.yandex.net/v1')

    limit_message = int(os.getenv('LIMIT_MESSAGE') or yaml_config.get('limit_message', 10))
    limit_chars = int(os.getenv('LIMIT_CHARS') or yaml_config.get('limit_chars', 2000))
    temperature = float(os.getenv('TEMPERATURE') or yaml_config.get('temperature', 0.7))
    system_prompt = os.getenv('SYSTEM_PROMPT') or yaml_config.get('system_prompt')

    if not api_key or not folder_id:
        print('Забыл указать API ключи в .env или конфиге!')
        exit(1)

    return Config(
        api_key=api_key,
        api_host=api_host,
        folder_id=folder_id,
        limit_message=limit_message,
        limit_chars=limit_chars,
        temperature=temperature,
        system_prompt=system_prompt
    )