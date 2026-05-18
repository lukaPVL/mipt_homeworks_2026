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
        try:
            with open('config.yaml', 'r', encoding='utf-8') as f:
                yaml_config = yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Не удалось прочитать config.yaml: {e}. Поставлены дифолтные настройки")

    api_key = os.getenv('YANDEX_API_KEY') or yaml_config.get('api_key')
    folder_id = os.getenv('YANDEX_FOLDER_ID') or yaml_config.get('folder_id')
    api_host = os.getenv('API_HOST') or yaml_config.get('api_host', 'https://llm.api.cloud.yandex.net/v1')

    limit_message = get_int('limit_message', 10, yaml_config)
    limit_chars = get_int('limit_chars', 2000, yaml_config)
    temperature = get_float('temperature', 0.7, yaml_config)
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

def get_int(key: str, default: int, yaml_config: dict) -> int:
    val = os.getenv(key.upper()) or yaml_config.get(key)
    try:
        return int(val) if val is not None else default
    except (ValueError, TypeError):
        return default

def get_float(key: str, default: float, yaml_config: dict) -> float:
    val = os.getenv(key.upper()) or yaml_config.get(key)
    try:
        return float(val) if val is not None else default
    except (ValueError, TypeError):
        return default
