# import assemblyai as aai
# from elevenlabs import generate, stream
# import os
# from openai import OpenAI

# class AI_Assistant:
#     def __init__(self):

#         aai.settings.api_key = "880ded64e29d44cda9aa8a271aa28cc5"
#         self.openai_client = OpenAI(api_key = "072acc652f0649bf8733fbee6eaf3ad9")
#         self.elevenlabs_api_key = "sk_4397423df5aeddf92a7d71c49cc4bbc6c221c75625d45a36"
        
#         self.transcriber = None
        
#         # Prompt
#         self.full_transcript = [
#         {"role":"system", "content":"You are a receptionist at a dental clinic. Be resourceful and efficient."},
#         ]
        
# ###### Step 2: Real-Time Transcription with AssemblyAI ######
#     def start_transcription(self):
#         print("Starting transcription...")
#         self.transcriber = aai.RealtimeTranscriber(
#             sample_rate = 16000,
#             on_data = self.on_data,
#             on_error = self.on_error,
#             on_open = self.on_open,
#             on_close = self.on_close,
#             end_utterance_silence_threshold = 1000
#         )
#         self.transcriber.connect()
#         microphone_stream = aai.extras.MicrophoneStream(sample_rate =16000)
#         print("microphone stream created", microphone_stream)
#         self.transcriber.stream(microphone_stream)
#         print("Listening...")
#     def stop_transcription(self):
#         print("Stopping transcription...")
#         if self.transcriber:
#             self.transcriber.close()
#             self.transcriber = None
            
#     def on_open(self, session_opened: aai.RealtimeSessionOpened):
#         # print("Session ID:", session_opened.session_id)
#         return


#     def on_data(self, transcript: aai.RealtimeTranscript):
#         if not transcript.text:
#             return

#         if isinstance(transcript, aai.RealtimeFinalTranscript):
#             self.generate_ai_response(transcript)
#         else:
#             print(transcript.text, end="\r")


#     def on_error(self, error: aai.RealtimeError):
#         # print("An error occured:", error)
#         return


#     def on_close(self):
#         #print("Closing Session")
#         return
        
#     def generate_ai_response(self, transcript):
#         self.stop_transcription()
        
#         self.full_transcript.append({"role":"user", "content":transcript.text}) 
#         print(f"\npatient: {transcript.text},",end="\r\n")
#         response = self.openai_client.chat.completions.create(
#             model="gpt-3.5-turbo",
#             messages=self.full_transcript,
#         )
        
#         ai_response = response.choices[0].message.content
        
#         self.generate_audio(ai_response)
#         self.start_transcription()
        
#     def generate_audio(self, text):
        
#         self.full_transcript.append({"role":"assistant", "content":text})
#         print(f"\nAI Receptionist: {text}")
        
#         audio_stream = generate(
#             api_key = self.elevenlabs_api_key,
#             text = text,
#             voice = "Rachel",
#             stream = True
#         )
#         # Set mpv path for Windows
#         os.environ['PATH'] += os.pathsep + os.getcwd()
#         stream(audio_stream)

# greeting ="Thankyou for calling the RSAM Dental Clinic. My Name is Aliya, How may i help You today?"

# ai_assistant = AI_Assistant()  
# ai_assistant.generate_audio(greeting)
# ai_assistant.start_transcription()         
        
# import os
# import logging
# from typing import Type

# import assemblyai as aai
# from assemblyai.streaming.v3 import (
#     BeginEvent,
#     StreamingClient,
#     StreamingClientOptions,
#     StreamingError,
#     StreamingEvents,
#     StreamingParameters,
#     StreamingSessionParameters,
#     TerminationEvent,
#     TurnEvent,
# )
# from openai import OpenAI
# from elevenlabs import generate, stream


# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)


# class AI_Assistant:
#     def __init__(self):
#         self.openai_client = OpenAI(api_key=OPENAI_KEY)
#         self.full_transcript = [
#             {"role": "system", "content": "You are a receptionist at a dental clinic. Be resourceful and efficient."}
#         ]

#         # Create AssemblyAI client
#         self.client = StreamingClient(
#             StreamingClientOptions(
#                 api_key=ASSEMBLY_KEY,
#                 api_host="streaming.assemblyai.com",
#             )
#         )

#         # Register AssemblyAI event handlers
#         self.client.on(StreamingEvents.Begin, self.on_begin)
#         self.client.on(StreamingEvents.Turn, self.on_turn)
#         self.client.on(StreamingEvents.Termination, self.on_terminated)
#         self.client.on(StreamingEvents.Error, self.on_error)

#     # ==============================
#     # AssemblyAI Handlers
#     # ==============================
#     def on_begin(self, _: Type[StreamingClient], event: BeginEvent):
#         print(f"Session started: {event.id}")

#     def on_turn(self, client: Type[StreamingClient], event: TurnEvent):
#         if not event.transcript:
#             return

#         if event.end_of_turn:
#             print(f"\nPatient: {event.transcript}")

#             # Send transcript to AI
#             self.full_transcript.append({"role": "user", "content": event.transcript})
#             response = self.openai_client.chat.completions.create(
#                 model="gpt-3.5-turbo",
#                 messages=self.full_transcript,
#             )
#             ai_response = response.choices[0].message.content

#             # Speak it out
#             self.generate_audio(ai_response)

#             # Store for context
#             self.full_transcript.append({"role": "assistant", "content": ai_response})

#             # Tell AssemblyAI to format turns properly
#             if not event.turn_is_formatted:
#                 params = StreamingSessionParameters(format_turns=True)
#                 client.set_params(params)

#     def on_terminated(self, _: Type[StreamingClient], event: TerminationEvent):
#         print(f"Session terminated: {event.audio_duration_seconds} sec audio processed")

#     def on_error(self, _: Type[StreamingClient], error: StreamingError):
#         print(f"Error: {error}")

#     # ==============================
#     # Audio Output (ElevenLabs)
#     # ==============================
#     def generate_audio(self, text):
#         print(f"\nAI Receptionist: {text}\n")
#         audio_stream = generate(
#             api_key=ELEVEN_KEY,
#             text=text,
#             voice="Rachel",
#             stream=True,
#         )
#         stream(audio_stream)

#     # ==============================
#     # Start/Stop Session
#     # ==============================
#     def start(self):
#         self.client.connect(
#             StreamingParameters(
#                 sample_rate=16000,
#                 format_turns=True,
#             )
#         )
#         try:
#             self.client.stream(
#                 aai.extras.MicrophoneStream(sample_rate=16000)
#             )
#         finally:
#             self.client.disconnect(terminate=True)


# # ==============================
# # MAIN
# # ==============================
# if __name__ == "__main__":
#     ai = AI_Assistant()
#     greeting = "Thank you for calling the RSAM Dental Clinic. My name is Aliya, how may I help you today?"
#     ai.generate_audio(greeting)
#     ai.start()

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

import google.generativeai as genai
from elevenlabs import generate, stream


# ==============================
# API KEYS
# ==============================
ASSEMBLY_KEY = ""
GEMINI_KEY = ""   # <-- replace with your free Gemini API key
ELEVEN_KEY = ""


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AI_Assistant:
    def __init__(self):
        # Gemini client
        genai.configure(api_key=GEMINI_KEY)
        self.gemini_model = genai.GenerativeModel("gemini-1.5-flash")

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

            # Append transcript to context
            self.full_transcript.append({"role": "user", "content": event.transcript})

            # Convert messages into a single prompt for Gemini
            prompt = "\n".join(
                f"{msg['role'].capitalize()}: {msg['content']}" for msg in self.full_transcript
            )

            # Get response from Gemini
            response = self.gemini_model.generate_content(prompt)
            ai_response = response.text.strip()

            # Speak it out
            self.generate_audio(ai_response)

            # Store assistant response
            self.full_transcript.append({"role": "assistant", "content": ai_response})

            # Tell AssemblyAI to format turns properly
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
        audio_stream = generate(
            api_key=ELEVEN_KEY,
            text=text,
            voice="Rachel",
            stream=True,
        )
        stream(audio_stream)

    # ==============================
    # Start/Stop Session
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
