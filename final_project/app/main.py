from config.config_loader import load_config
from service.llm_service import LLMService
from service.context_service import ContextService
from service.file_service import FileService
from service.chat_service import ChatService
from controller.chat_controller import ChatController


def main():
    config = load_config()

    llm_service = LLMService(
        api_key=config.api_key,
        folder_id=config.folder_id,
        api_host=config.api_host,
        temperature=config.temperature
    )

    context_service = ContextService(
        limit_message=config.limit_message,
        limit_chars=config.limit_chars
    )

    file_service = FileService(max_size_mb=5)

    chat_service = ChatService(
        llm_service=llm_service,
        context_service=context_service,
        file_service=file_service,
        system_prompt=config.system_prompt
    )

    controller = ChatController(chat_service)
    controller.run()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nПока!')
        exit(0)
