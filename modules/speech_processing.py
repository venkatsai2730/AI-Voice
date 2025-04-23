class DeepgramTranscriber:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.deepgram.com/v1/listen"

    def transcribe(self, audio_file):
        """Transcribe audio file using Deepgram."""
        headers = {"Authorization": f"Token {self.api_key}"}
        with open(audio_file, "rb") as audio:
            response = requests.post(
                self.base_url,
                headers=headers,
                data=audio,
                params={"model": "general", "language": "en-US", "punctuate": "true"}
            )
        if response.status_code == 200:
            result = response.json()
            transcript = result["results"]["channels"][0]["alternatives"][0]["transcript"]
            return transcript
        logging.error(f"Deepgram error: {response.status_code} - {response.text}")
        return ""