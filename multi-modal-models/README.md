# Multi-Modal Models

A directory of multi-modal recipes from the [Microsoft Foundry Forgebook](https://microsoft-foundry.github.io/forgebook/) — runnable Jupyter notebook recipes for image generation, speech synthesis, and audio transcription using MAI models on Microsoft Foundry.

---

## Image Generation

| Recipe | Description | Tags |
|--------|-------------|------|
| [Build a Production Editing Recipe with MAI-Image-2.5](https://microsoft-foundry.github.io/forgebook/notebook/mai-image-2-5/) | Private-preview MAI-Image-2.5 notebook covering text-to-image generation, image edits, safety reminders, and troubleshooting. | `mai` `models` `inference` `image-generation` `multimodal` |
| [Generate Images with MAI-Image-2 and MAI-Image-2e](https://microsoft-foundry.github.io/forgebook/notebook/mai-image-2/) | MAI-Image-2 and MAI-Image-2e text-to-image notebook with prompt variations, parameter tuning, and token-based cost calculations. | `mai` `models` `inference` `image-generation` `multimodal` |
| [Call MAI-Image-2 from a Foundry Deployment](https://microsoft-foundry.github.io/forgebook/notebook/mai-image-2-foundry/) | Foundry-focused MAI-Image-2 notebook covering deployment-based calls, prompt variants, and cost breakdown. | `mai` `models` `inference` `image-generation` `multimodal` |

---

## Speech & Audio

| Recipe | Description | Tags |
|--------|-------------|------|
| [Build a Multilingual Text-to-Speech Recipe with MAI-Voice-2](https://microsoft-foundry.github.io/forgebook/notebook/mai-voice-2/) | MAI-Voice-2 notebook with key-auth REST calls, multilingual speakers, expressive SSML, and cost calculator patterns. | `mai` `models` `inference` `speech` `text-to-speech` `audio-generation` |
| [Generate Speech with MAI-Voice-1](https://microsoft-foundry.github.io/forgebook/notebook/mai-voice-1-foundry/) | MAI-Voice-1 notebook using Foundry endpoint with REST and SDK patterns, long-form synthesis, and character-based cost estimation. | `mai` `models` `inference` `text-to-speech` `audio-generation` |
| [Build Speech-to-Text with MAI-Transcribe-1.5](https://microsoft-foundry.github.io/forgebook/notebook/mai-transcribe-1-5/) | Speech API multipart cookbook for MAI-Transcribe-1.5 covering baseline transcription, verbatim mode, phrase-list entity biasing, and language identification. | `mai` `models` `inference` `speech` `transcription` `audio` |
| [Transcribe Audio with MAI-Transcribe-1](https://microsoft-foundry.github.io/forgebook/notebook/mai-transcribe-1-foundry/) | Entra-first MAI-Transcribe-1 notebook with Foundry endpoint setup, local audio transcription, diarization, translation, and cost estimation. | `mai` `models` `inference` `speech` `transcription` `audio` |

---

## Video Generation

| Recipe | Description | Tags |
|--------|-------------|------|
| [Guide Sora 2 with Images and Audio](https://microsoft-foundry.github.io/forgebook/notebook/sora-video-generation-rest-api/) | Use Azure OpenAI REST calls to generate a Sora 2 clip, reuse a frame as an image reference, and add ambient audio. | `azure-openai` `video` `video-generation` `audio` `audio-generation` `multimodal` `responsible-ai` |

---

## Resources

- **Forgebook**: [microsoft-foundry.github.io/forgebook](https://microsoft-foundry.github.io/forgebook/)
- **Source**: [github.com/microsoft-foundry/forgebook](https://github.com/microsoft-foundry/forgebook)
- **Quick start**: `git clone https://github.com/microsoft-foundry/forgebook.git && cd forgebook && pip install -r requirements.txt && jupyter notebook`
