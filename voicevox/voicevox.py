from core.model_runtime.model_providers.__base.model_provider import ModelProvider

class VoicevoxProvider(ModelProvider):
    def validate_provider_credentials(self, credentials) -> None:
        # Just implemented to prevent `Not implemented` error.
        pass
