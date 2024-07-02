import concurrent.futures
from functools import reduce
from io import BytesIO
from typing import Optional
from flask import Response
from pydub import AudioSegment
import httpx
from core.model_runtime.model_providers.__base.tts_model import TTSModel
from core.model_runtime.errors.validate import CredentialsValidateFailedError
from core.model_runtime.errors.invoke import (
    InvokeBadRequestError,
    InvokeError,
    InvokeServerUnavailableError,
)


class VoicevoxText2SpeechModel(TTSModel):
    """
    Model class for VOICEVOX Speech to text model.
    """

    def _invoke(self, model: str, tenant_id: str, credentials: dict,
                content_text: str, voice: str, streaming: bool, user: Optional[str] = None) -> any:
        if not voice or voice not in [d["value"] for d in self.get_tts_model_voices(model=model, credentials=credentials)]:
            voice = self._get_model_default_voice(model, credentials)
        return self._tts_invoke(model=model, credentials=credentials, content_text=content_text, voice=voice)

    def validate_credentials(self, model: str, credentials: dict, user: Optional[str] = None) -> None:
        try:
            self._tts_invoke(
                model=model,
                credentials=credentials,
                content_text="こんにちは。",
                voice=self._get_model_default_voice(model, credentials),
            )
        except Exception as ex:
            raise CredentialsValidateFailedError(str(ex))

    def _tts_invoke(self, model: str, credentials: dict, content_text: str, voice: str) -> Response:
        audio_type = self._get_model_audio_type(model, credentials)
        word_limit = self._get_model_word_limit(model, credentials)
        max_workers = self._get_model_workers_limit(model, credentials)
        try:
            sentences = list(self._split_text_into_sentences(text=content_text, limit=word_limit))
            audio_bytes_list = []

            # Create a thread pool and map the function to the list of sentences
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(self._process_sentence, sentence=sentence, voice=voice,
                                           api_base=credentials["voicevox_api_base"]) for sentence in sentences]
                for future in futures:
                    try:
                        if future.result():
                            audio_bytes_list.append(future.result())
                    except Exception as ex:
                        raise InvokeBadRequestError(str(ex))

            if len(audio_bytes_list) > 0:
                audio_segments = [AudioSegment.from_file(BytesIO(audio_bytes), format=audio_type) for audio_bytes in
                                  audio_bytes_list if audio_bytes]
                combined_segment = reduce(lambda x, y: x + y, audio_segments)
                buffer: BytesIO = BytesIO()
                combined_segment.export(buffer, format=audio_type)
                buffer.seek(0)
                return Response(buffer.read(), status=200, mimetype=f"audio/{audio_type}")

        except Exception as ex:
            raise InvokeBadRequestError(str(ex))

    def _process_sentence(self, sentence: str, voice: str, api_base: str):
        with httpx.Client() as client:
            query_resp = client.post(api_base + "/audio_query", params={"speaker": voice, "text": sentence.strip()})
            audio_query = query_resp.json()
            audio_resp = client.post(api_base + "/synthesis", params={"speaker": voice}, json=audio_query)
            if isinstance(audio_resp.content, bytes):
                return audio_resp.content

    @property
    def _invoke_error_mapping(self) -> dict[type[InvokeError], list[type[Exception]]]:
        # TODO: Break down the errors
        return {
            InvokeServerUnavailableError: [Exception],
        }
