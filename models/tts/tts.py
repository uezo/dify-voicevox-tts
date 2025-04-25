from collections.abc import Generator
from typing import Optional

import concurrent.futures
from io import BytesIO
from typing import Optional
from pydub import AudioSegment
import httpx

from dify_plugin import TTSModel
from dify_plugin.errors.model import (
    CredentialsValidateFailedError,
    InvokeBadRequestError,
    InvokeError,
    InvokeServerUnavailableError
)


class VoicevoxText2SpeechModel(TTSModel):
    """
    Model class for OpenAI Speech to text model.
    """

    def _invoke(
        self,
        model: str,
        tenant_id,
        credentials: dict,
        content_text: str,
        voice: str,
        user: Optional[str] = None,
    ) -> bytes | Generator[bytes, None, None]:
        """
        _invoke text2speech model

        :param model: model name
        :param tenant_id: user tenant id
        :param credentials: model credentials
        :param content_text: text content to be translated
        :param voice: model timbre
        :param user: unique user id
        :return: text translated to audio file
        """
        if not voice or voice not in [d["value"] for d in self.get_tts_model_voices(model=model, credentials=credentials)]:
            voice = self._get_model_default_voice(model, credentials)
        return self._tts_invoke(model=model, credentials=credentials, content_text=content_text, voice=voice)

    def validate_credentials(
        self, model: str, credentials: dict, user: Optional[str] = None
    ) -> None:
        """
        validate credentials text2speech model

        :param model: model name
        :param credentials: model credentials
        :param user: unique user id
        :return: text translated to audio file
        """
        try:
            next(self._tts_invoke(
                model=model,
                credentials=credentials,
                content_text="こんにちは。",
                voice=self._get_model_default_voice(model, credentials),
            ))
        except Exception as ex:
            raise CredentialsValidateFailedError(str(ex))
        
    def _tts_invoke(self, model: str, credentials: dict, content_text: str, voice: str) -> any:
        audio_type = self._get_model_audio_type(model, credentials)
        word_limit = self._get_model_word_limit(model, credentials)
        max_workers = self._get_model_workers_limit(model, credentials)
        try:
            sentences = list(self._split_text_into_sentences(org_text=content_text, max_length=word_limit))
            # Create a thread pool and map the function to the list of sentences
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(self._process_sentence, sentence=sentence, voice=voice,
                                           api_base=credentials["voicevox_api_base"]) for sentence in sentences]
                for future in futures:
                    if future.result():
                        buffer: BytesIO = BytesIO()
                        segment = AudioSegment.from_file(BytesIO(future.result()), format=audio_type)
                        segment.export(buffer, format="mp3")
                        buffer.seek(0)
                        yield buffer.read()
        except Exception as ex:
            raise InvokeBadRequestError(str(ex))
        
    def _process_sentence(self, sentence: str, voice: str, api_base: str):
        with httpx.Client() as client:
            query_resp = client.post(api_base + "/audio_query", params={"speaker": voice, "text": sentence.strip()},timeout=30.0)
            audio_query = query_resp.json()
            audio_resp = client.post(api_base + "/synthesis", params={"speaker": voice}, json=audio_query, timeout=30.0)
            if isinstance(audio_resp.content, bytes):
                return audio_resp.content
     
    @property
    def _invoke_error_mapping(self) -> dict[type[InvokeError], list[type[Exception]]]:
        # TODO: Break down the errors
        return {
            InvokeServerUnavailableError: [Exception],
        }