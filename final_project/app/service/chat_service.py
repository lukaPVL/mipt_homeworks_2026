from dto.chat_dto import ChatResponseDto

class ChatService:
    def __init__(self, llm_service, context_service, file_service, system_prompt: str = None):
        self.llm_service = llm_service
        self.context_service = context_service
        self.file_service = file_service
        self.system_prompt = system_prompt

    def send_message(self, user_text: str) -> ChatResponseDto:
        processed_text = self.file_service.process_user_input(user_text)
        self.context_service.prepare_and_add_user_message(processed_text)
        try:
            response_content = self.llm_service.get_completion(
                system_prompt=self.system_prompt,
                messages=self.context_service.get_history()
            )
            self.context_service.add_message(role='assistant', content=response_content)
            return ChatResponseDto(content=response_content, success=True)

        except Exception as e:
            return ChatResponseDto(content='', success=False, error_message=str(e))

    def reset_chat(self):
        self.context_service.reset()