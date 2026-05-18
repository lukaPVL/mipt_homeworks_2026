import os
import re


class FileService:
    def __init__(self, max_size_mb=5):
        self.max_size_bytes = max_size_mb * 1024 * 1024

    def process_user_input(self, text):
        return re.sub(r'@::(.*?)::', self._replace_match, text)

    def _replace_match(self, match):
        filepath = match.group(1).strip()

        if not os.path.exists(filepath):
            return f'\nОшибка: файл {filepath} не найден\n'

        if os.path.getsize(filepath) > self.max_size_bytes:
            return f'\nОшибка: файл {filepath} слишком большой (лимит 5МБ)\n'

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f'\n{f.read()}\n'
        except Exception as e:
            return f'\nНе удалось прочитать {filepath}: {e}\n'

    def get_chunks(self, filepath, command_line):
        content = self.read_file(filepath)

        if 'len=' in command_line:
            parts = command_line.split('len=')
            length = int(parts[1].split()[0])

            chunks = []
            for i in range(0, len(content), length):
                chunks.append(content[i:i + length])
            return chunks

        elif 'paragraph=' in command_line:
            parts = command_line.split('paragraph=')
            num_p = int(parts[1].split()[0])

            all_lines = content.split('\n')
            chunks = []
            for i in range(0, len(all_lines), num_p):
                chunks.append('\n'.join(all_lines[i:i + num_p]))
            return chunks

        else:
            return [line for line in content.split('\n') if line.strip()]

    def read_file(self, filepath):
        if not os.path.exists(filepath):
            raise Exception(f'Файл {filepath} не существует')
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
