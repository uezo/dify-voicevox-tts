# dify-voicevox-tts

An experimental implementation of VOICEVOX text-to-speech custom model for Dify.

## 📦 Installation

- Download this repo.
- Copy the voicevox directory to `api/core/model_runtime/model_providers` in the API server.
- Restart the API server.

If you are not able to build the API server container image yourself, you can copy the directory to the container and save it with the following steps:

```sh
docker cp /path/to/voicevox <container id>:/app/api/core/model_runtime/model_providers
docker commit <container id>
```


## ✨ Add model

Set up VOICEVOX in the list of model providers. The URL must be reachable from the inside of the API container. `http://127.0.0.1:50021` doesn't work without any network configurations.

![Add model](resources/settings.png)


## 🥳 Use TTS feature

Click [Features] > [+ Add Feature] and turn on `Text to Speech`.

![Add feature](resources/addfeature.png)

Enjoy👍


## 🙏 I NEED YOUR CONTRIBUTION

This is just an experimental implementation, and we need your help to make it better. Please contribute! 🚀✨
