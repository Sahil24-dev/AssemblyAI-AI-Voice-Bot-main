import os
import logging
from typing import Type

import assemblyai as aai
from assemblyai.streaming.v3 import (
    BeginEvent,
    StreamingClient,
    StreamingClientOptions,
    StreamingError,
    StreamingEvents,
    StreamingParameters,
    StreamingSessionParameters,
    TerminationEvent,
    TurnEvent,
)
from elevenlabs import generate, stream

# Install google generative AI SDK:
# pip install google-genai

import google.generativeai as genai

from elevenlabs.client import ElevenLabs
from elevenlabs import stream as play

# ==============================
# API KEYS
# ==============================
ASSEMBLY_KEY = os.getenv("880ded64e29d44cda9aa8a271aa28cc5")
GEMINI_KEY = os.getenv("AIzaSyBuk6rpzdWpq0hbn9l7sxsLAAOF64d1TVI")
ELEVEN_KEY = os.getenv("sk_4397423df5aeddf92a7d71c49cc4bbc6c221c75625d45a36")


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AI_Assistant:
    def __init__(self):
        # configure Gemini
        genai.configure(api_key=GEMINI_KEY)

        self.full_transcript = [
            {"role": "system", "content": "You are a receptionist at a dental clinic. Be resourceful and efficient."}
        ]

        # Create AssemblyAI client
        self.client = StreamingClient(
            StreamingClientOptions(
                api_key=ASSEMBLY_KEY,
                api_host="streaming.assemblyai.com",
            )
        )

        # Register AssemblyAI event handlers
        self.client.on(StreamingEvents.Begin, self.on_begin)
        self.client.on(StreamingEvents.Turn, self.on_turn)
        self.client.on(StreamingEvents.Termination, self.on_terminated)
        self.client.on(StreamingEvents.Error, self.on_error)
        self.eleven_client = ElevenLabs(api_key=ELEVEN_KEY)


    # ==============================
    # AssemblyAI Handlers
    # ==============================
    def on_begin(self, _: Type[StreamingClient], event: BeginEvent):
        print(f"Session started: {event.id}")

    def on_turn(self, client: Type[StreamingClient], event: TurnEvent):
        if not event.transcript:
            return

        if event.end_of_turn:
            print(f"\nPatient: {event.transcript}")

            # Send transcript to Gemini instead of OpenAI
            self.full_transcript.append({"role": "user", "content": event.transcript})

            # Using Gemini (chat-like model) - adjust model name and SDK call as needed
            resp = genai.ChatCompletion.create(
                model="gemini-1.5-flash",  # or "gemini-2.5-flash" etc., depending on free tier and availability
                messages=self.full_transcript
            )
            ai_response = resp.choices[0].message.content

            # Speak it out
            self.generate_audio(ai_response)

            # Store for context
            self.full_transcript.append({"role": "assistant", "content": ai_response})

            # Format turns
            if not event.turn_is_formatted:
                params = StreamingSessionParameters(format_turns=True)
                client.set_params(params)

    def on_terminated(self, _: Type[StreamingClient], event: TerminationEvent):
        print(f"Session terminated: {event.audio_duration_seconds} sec audio processed")

    def on_error(self, _: Type[StreamingClient], error: StreamingError):
        print(f"Error: {error}")

    # ==============================
    # Audio Output (ElevenLabs)
    # ==============================
    def generate_audio(self, text):
        print(f"\nAI Receptionist: {text}\n")
        audio_stream = self.eleven_client.text_to_speech.convert(
            voice_id="Rachel",  # Or another voice from your account
            model_id="eleven_multilingual_v2",
            text=text,
            stream=True,
        )

        play(audio_stream)

    # ==============================
    # Start Session
    # ==============================
    def start(self):
        self.client.connect(
            StreamingParameters(
                sample_rate=16000,
                format_turns=True,
            )
        )
        try:
            self.client.stream(
                aai.extras.MicrophoneStream(sample_rate=16000)
            )
        finally:
            self.client.disconnect(terminate=True)


# ==============================
# MAIN
# ==============================
if __name__ == "__main__":
    ai = AI_Assistant()
    greeting = "Thank you for calling the RSAM Dental Clinic. My name is Aliya, how may I help you today?"
    ai.generate_audio(greeting)
    ai.start()