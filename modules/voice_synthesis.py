import requests
import base64
import logging

class ElevenLabsVoice:
    def __init__(self, api_key, voice_id):
        self.api_key = api_key
        self.voice_id = voice_id
        self.base_url = "https://api.elevenlabs.io/v1"

    def synthesize(self, text):
        """Convert text to speech using ElevenLabs API."""
        url = f"{self.base_url}/text-to-speech/{self.voice_id}"
        headers = {"xi-api-key": self.api_key, "Content-Type": "application/json"}
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.7, "similarity_boost": 0.5}
        }
        
        try:
            logging.debug(f"Sending request to ElevenLabs: {text[:50]}...")
            response = requests.post(url, json=data, headers=headers, timeout=10)
            response.raise_for_status()  # Raise for 4xx/5xx errors
            audio_content = response.content
            logging.debug(f"Received audio content length: {len(audio_content)} bytes")
            
            audio_base64 = base64.b64encode(audio_content).decode('utf-8')
            audio_url = f"data:audio/mpeg;base64,{audio_base64}"
            logging.debug(f"Generated audio URL length: {len(audio_url)} chars, starts with: {audio_url[:50]}...")
            
            return audio_url
        except requests.RequestException as e:
            logging.error(f"ElevenLabs API error: {e}, response: {response.text if 'response' in locals() else 'N/A'}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error in synthesize: {e}")
            raise