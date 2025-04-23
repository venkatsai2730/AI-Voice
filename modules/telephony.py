from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream

class TelephonyHandler:
    def __init__(self, account_sid, auth_token, phone_number, webhook_url):
        self.client = Client(account_sid, auth_token)
        self.phone_number = phone_number
        self.webhook_url = webhook_url

    def place_call(self, to, webhook_url=None):
        if webhook_url is None:
            webhook_url = self.webhook_url
        call = self.client.calls.create(
            url=f"{webhook_url}/webhook/incoming-call",
            to=to,
            from_=self.phone_number
        )
        return call

    def connect_to_stream(self):
        """Set up Twilio Stream for real-time transcription and synthesis."""
        response = VoiceResponse()
        connect = Connect(action=f"{self.webhook_url}/webhook/call-status")
        
        # WebSocket stream for real-time audio
        stream = Stream(
            url=f"wss://{self.webhook_url.split('https://')[1]}/webhook/stream",
            name="AI Sales Agent Stream"
        )
        connect.append(stream)
        
        response.append(connect)
        return response