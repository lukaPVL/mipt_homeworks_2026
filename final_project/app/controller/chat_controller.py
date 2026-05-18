import os
from dto.chat_dto import ChatResponseDto
from dto.chat_dto import MessageDto


class ChatController:
    def __init__(self, chat_service):
        self.chat_service = chat_service

    def run(self):
        print('Команды: \\q - выход, /reset - новый чат, /file_chunk - обработка файла')

        while True:
            try:
                user_input = input('\n Я: ').strip()
                if not user_input:
                    continue

                if user_input == '\\q':
                    print('Выход из программы...')
                    break

                if user_input == '/reset':
                    self._handle_reset()
                    continue

                if user_input.startswith('/file_chunk'):
                    self._process_chunks(user_input)
                    continue

                self._send_to_llm(user_input)

            except EOFError:
                break
            except Exception as e:
                print(f'Произошла ошибка: {e}')

    def _send_to_llm(self, text: str):
        try:
            print('Отправляю запрос...')
            response: ChatResponseDto = self.chat_service.send_message(text)

            if response.success:
                print(f'Бот: {response.content}')
            else:
                print(f'Ошибка: {response.error_message}')

        except KeyboardInterrupt:
            print('\n Запрос прерван')

    def _handle_reset(self):
        self.chat_service.reset_chat()
        command = 'cls' if os.name == 'nt' else 'clear'
        os.system(command)
        print('Чат сброшен')

    def _process_chunks(self, command_line: str):
        try:
            filepath = input('Путь к файлу: ').strip()
            if not filepath:
                return
            if not os.path.exists(filepath):
                print('Ошибка: Файл не найден.')
                return

            user_prompt = input('Задание для нейронки: \n ')
            if not user_prompt:
                user_prompt = 'Проанализируй этот текст.'

            chunks = self.chat_service.file_service.get_chunks(filepath, command_line)
            auto_mode = '-y' in command_line
            print(f'Ок, делю на части. Всего вышло: {len(chunks)} шт.')

            for i, chunk in enumerate(chunks):
                if not chunk.strip():
                    continue

                full_query = f'{user_prompt}\n\nТекст для обработки:\n{chunk}'

                try:
                    response = self.chat_service.llm_service.get_completion(
                        system_prompt=None,
                        messages=[MessageDto(role='user', content=full_query)]
                    )
                    print(f'\n[Чанк {i + 1}]:\n{response}')
                except KeyboardInterrupt:
                    print('\nОбработка чанков прервана')
                    break

                if not auto_mode and i < len(chunks) - 1:
                    try:
                        input('\nНажмите enter для следующего чанка...')
                    except KeyboardInterrupt:
                        print('\nВыход из режима чанков')
                        break

        except KeyboardInterrupt:
            print('\n[Операция отменена]')
        except Exception as e:
            print(f'Ошибка при обработке файла: {e}')
