import os
from flask import Flask, request, jsonify
from twilio.twiml.voice_response import VoiceResponse, Gather
from modules.telephony import TelephonyHandler
from modules.speech_processing import DeepgramTranscriber
from modules.voice_synthesis import ElevenLabsVoice
from modules.data_storage import ConversationLogger
from modules.conversation import ConversationEngine
from dotenv import load_dotenv
import logging
import base64
import requests

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize modules
telephony = TelephonyHandler(
    account_sid=os.getenv("TWILIO_ACCOUNT_SID"),
    auth_token=os.getenv("TWILIO_AUTH_TOKEN"),
    phone_number=os.getenv("TWILIO_PHONE_NUMBER"),
    webhook_url="https://f448-2a09-bac1-36c0-40-00-1ae-3.ngrok-free.app"
)

transcriber = DeepgramTranscriber(api_key=os.getenv("DEEPGRAM_API_KEY"))
conversation_engine = ConversationEngine(model_name="microsoft/DialoGPT-medium")
voice_synthesizer = ElevenLabsVoice(api_key=os.getenv("ELEVENLABS_API_KEY"), voice_id=os.getenv("ELEVENLABS_VOICE_ID"))
logger = ConversationLogger(db_connection=os.getenv("DATABASE_URL", "conversations.db"))

# Sales agent prompt
SALES_AGENT_PROMPT = """
You are an AI sales representative named Alex. Greet the customer professionally, introduce yourself, 
and ask how you can assist them today. Maintain a friendly, concise, and helpful tone.
"""
conversation_engine.add_message("assistant", SALES_AGENT_PROMPT)

# Initialize database tables
with app.app_context():
    logger.create_tables()

@app.route("/webhook/incoming-call", methods=["POST"])
def incoming_call():
    """Handle incoming Twilio calls."""
    logging.info("Incoming call received")
    call_sid = request.form.get("CallSid")
    caller = request.form.get("From")
    logger.log_call_start(call_sid, caller)

    response = VoiceResponse()
    initial_greeting = "Hello! This is Alex, your AI assistant. How can I help you today?"
    response.say(initial_greeting, voice="Polly.Joanna")
    logger.log_message(call_sid, "assistant", initial_greeting)
    
    gather = Gather(
        input="speech",
        action=f"{telephony.webhook_url}/webhook/gather",
        method="POST",
        speechTimeout="auto",
        language="en-US",
        hints="sales, products, pricing"
    )
    response.append(gather)
    
    logging.debug(f"TwiML response: {str(response)}")
    return str(response)

@app.route("/webhook/call-status", methods=["POST"])
def call_status():
    """Track call status updates."""
    call_sid = request.form.get("CallSid")
    status = request.form.get("CallStatus")
    logging.info(f"Call {call_sid} status: {status}")
    
    if status == "completed":
        logger.log_call_end(call_sid)
    
    return "", 200

@app.route("/webhook/gather", methods=["POST"])
def gather_handler():
    """Handle speech input from Gather."""
    call_sid = request.form.get("CallSid")
    speech_result = request.form.get("SpeechResult", "")

    response = VoiceResponse()
    try:
        if speech_result:
            logging.info(f"Speech input received: {speech_result}")
            response_text = conversation_engine.generate_response(speech_result)
            logger.log_message(call_sid, "user", speech_result)
            logger.log_message(call_sid, "assistant", response_text)
            
            logging.debug(f"Generating audio for: {response_text[:50]}...")
            audio_url = voice_synthesizer.synthesize(response_text)
            logging.debug(f"Generated audio URL: {audio_url[:50]}... (length: {len(audio_url)})")
            
            if audio_url.startswith("data:audio/mpeg;base64,"):
                response.play(audio_url)
                logging.info(f"Played response: {response_text}")
            else:
                logging.error(f"Invalid audio URL format: {audio_url[:50]}...")
                raise ValueError("Invalid audio URL format")
        else:
            response.say("I didn’t catch that. How can I assist you?", voice="Polly.Joanna")
    except Exception as e:
        logging.error(f"Error in gather handler: {e}")
        fallback_text = response_text if 'response_text' in locals() else "Sorry, I encountered an issue. How can I assist you?"
        response.say(fallback_text, voice="Polly.Joanna")

    # Loop back to gather more input
    gather = Gather(
        input="speech",
        action=f"{telephony.webhook_url}/webhook/gather",
        method="POST",
        speechTimeout="auto",
        language="en-US",
        hints="sales, products, pricing"
    )
    response.append(gather)
    
    logging.debug(f"TwiML response: {str(response)}")
    return str(response)

@app.route("/api/make-call", methods=["POST"])
def make_outbound_call():
    """Initiate an outbound call."""
    data = request.json
    to_number = data.get("to")
    
    if not to_number:
        return jsonify({"error": "Missing 'to' phone number"}), 400
    
    try:
        call = telephony.place_call(to=to_number)
        return jsonify({"status": "initiated", "call_sid": call.sid})
    except Exception as e:
        logging.error(f"Failed to initiate call: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)