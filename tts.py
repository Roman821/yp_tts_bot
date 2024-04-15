from requests import Session, post

from get_logger import get_logger


class TTS:

    def __init__(self, api_key: str, folder_id: str):

        self.api_key = api_key
        self.folder_id = folder_id
        self.logger = get_logger('main')

    def ask(self, text: str) -> bytes | str:
        """Returns bytes if success and string else"""

        error_message = 'Произошла ошибка, пожалуйста, повторите попытку или обратитесь в поддержку'

        try:
            response = post(
                'https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize',
                headers={
                    'Authorization': f'Api-Key {self.api_key}',
                },
                data={
                    'text': text,
                    'lang': 'ru-RU',
                    'voice': 'filipp',
                    'folderId': self.folder_id,
                },
            )

        except Exception as e:

            self.logger.error(f'An exception occurred while requesting tts answer ({text=}): {e}')

            return error_message

        response_status_code = response.status_code

        if response_status_code != 200:

            self.logger.error(f'Incorrect tts answer status code: {response_status_code} ({text=})')

            return error_message

        return response.content
