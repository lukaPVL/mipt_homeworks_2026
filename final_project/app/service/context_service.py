from dto.chat_dto import MessageDto


class ContextService:
    def __init__(self, limit_message: int, limit_chars: int):
        self.limit_message = limit_message
        self.limit_chars = limit_chars
        self._history: list = []

    def get_history(self) -> list[MessageDto]:
        return self._history

    def add_message(self, role: str, content: str):
        self._history.append(MessageDto(role=role, content=content))

    def prepare_and_add_user_message(self, text: str):
        text = text.strip()
        if not text:
            return

        if len(text) > self.limit_chars:
            text = text[-self.limit_chars:]

        while len(self._history) >= self.limit_message:
            self._history.pop(0)

        while sum(len(message.content) for message in self._history) + len(text) > self.limit_chars:
            if self._history:
                self._history.pop(0)
            else:
                break

        self.add_message(role='user', content=text)

    def reset(self):
        self._history = []
