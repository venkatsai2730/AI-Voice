from transformers import pipeline
from time import sleep
import logging

class ConversationEngine:
    def __init__(self, model_name="microsoft/DialoGPT-medium", max_history_length=5):
        try:
            self.model = pipeline("text-generation", model=model_name, device=-1)  # Use CPU
            logging.info(f"Successfully loaded model: {model_name}")
        except Exception as e:
            logging.error(f"Failed to load model {model_name}: {e}")
            raise
        self.conversation_history = []
        self.max_history_length = max_history_length

    def add_message(self, role, content):
        self.conversation_history.append({"role": role, "content": content})
        if len(self.conversation_history) > self.max_history_length * 2:
            self.conversation_history = self.conversation_history[-self.max_history_length * 2:]

    def generate_response(self, user_input):
        self.add_message("user", user_input)
        conversation = "\n".join([f"{item['role']}: {item['content']}" for item in self.conversation_history])
        response_text = self.call_huggingface_with_retry(conversation)
        self.add_message("assistant", response_text)
        return response_text

    def call_huggingface_with_retry(self, conversation, max_retries=3, delay=5):
        retries = 0
        while retries < max_retries:
            try:
                response = self.model(conversation, max_new_tokens=50, truncation=True)
                return response[0]['generated_text'].split(": ", 1)[-1].strip()
            except Exception as e:
                logging.error(f"Error calling Hugging Face model: {e}")
                sleep(delay)
                retries += 1
        raise Exception("Max retries exceeded for Hugging Face model.")