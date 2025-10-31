import os
import logging
import base64
import io
import threading
import time
from typing import Type
import json

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
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import wave
import tempfile

# ==============================
# API KEYS
# ==============================
ASSEMBLY_KEY = "880ded64e29d44cda9aa8a271aa28cc5"
GEMINI_KEY = "AIzaSyBuk6rpzdWpq0hbn9l7sxsLAAOF64d1TVI"
ELEVEN_KEY = "sk_4397423df5aeddf92a7d71c49cc4bbc6c221c75625d45a36"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app setup
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dental_clinic_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

class AI_Assistant:
    def __init__(self):
        # Gemini client
        genai.configure(api_key=GEMINI_KEY)
        self.gemini_model = genai.GenerativeModel("gemini-1.5-flash")

        self.full_transcript = [
            {"role": "system", "content": "You are a receptionist at a dental clinic. Be resourceful and efficient. Keep responses conversational and helpful."}
        ]

        # For web-based usage, we'll use AssemblyAI's regular transcription API instead of streaming
        aai.settings.api_key = ASSEMBLY_KEY
        
        self.current_session_id = None

    def transcribe_audio_file(self, audio_file_path):
        """Transcribe audio file using AssemblyAI"""
        try:
            transcriber = aai.Transcriber()
            transcript = transcriber.transcribe(audio_file_path)
            
            if transcript.status == aai.TranscriptStatus.error:
                logger.error(f"Transcription error: {transcript.error}")
                return None
            
            return transcript.text
        except Exception as e:
            logger.error(f"Error in transcription: {e}")
            return None
        finally:
            # Ensure file handle is released
            import gc
            gc.collect()

    def generate_ai_response(self, user_input):
        """Generate AI response using Gemini"""
        try:
            # Add user input to conversation history
            self.full_transcript.append({"role": "user", "content": user_input})

            # Convert messages into a single prompt for Gemini
            prompt = "\n".join(
                f"{msg['role'].capitalize()}: {msg['content']}" for msg in self.full_transcript
            )

            # Get response from Gemini
            response = self.gemini_model.generate_content(prompt)
            ai_response = response.text.strip()

            # Add AI response to conversation history
            self.full_transcript.append({"role": "assistant", "content": ai_response})

            return ai_response
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return "I apologize, but I'm having trouble processing your request right now. Please try again."

    def generate_audio_base64(self, text):
        """Generate audio and return as base64 string"""
        try:
            audio_stream = generate(
                api_key=ELEVEN_KEY,
                text=text,
                voice="Rachel",
                stream=False,  # Get complete audio instead of streaming
            )
            
            # Convert audio to base64
            audio_base64 = base64.b64encode(audio_stream).decode('utf-8')
            return audio_base64
        except Exception as e:
            logger.error(f"Error generating audio: {e}")
            return None

# Initialize AI Assistant
ai_assistant = AI_Assistant()

@app.route('/')
def index():
    """Serve the main page"""
    
    return render_template('index.html')


@app.route('/api/text-message', methods=['POST'])
def handle_text_message():
    """Handle text-based messages"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Empty message'}), 400

        # Generate AI response
        ai_response = ai_assistant.generate_ai_response(user_message)
        
        # Generate audio for the response
        audio_base64 = ai_assistant.generate_audio_base64(ai_response)
        
        return jsonify({
            'response': ai_response,
            'audio': audio_base64
        })
    
    except Exception as e:
        logger.error(f"Error in text message handler: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/audio-message', methods=['POST'])
def handle_audio_message():
    """Handle audio-based messages"""
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        
        # Save audio to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            audio_file.save(tmp_file.name)
            
            # Transcribe audio
            transcribed_text = ai_assistant.transcribe_audio_file(tmp_file.name)
            
            # Clean up temporary file
            os.unlink(tmp_file.name)
        
        if not transcribed_text:
            return jsonify({'error': 'Could not transcribe audio'}), 400

        # Generate AI response
        ai_response = ai_assistant.generate_ai_response(transcribed_text)
        
        # Generate audio for the response
        audio_base64 = ai_assistant.generate_audio_base64(ai_response)
        
        return jsonify({
            'transcribed_text': transcribed_text,
            'response': ai_response,
            'audio': audio_base64
        })
    
    except Exception as e:
        logger.error(f"Error in audio message handler: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('Client connected')
    emit('status', {'message': 'Connected to RSAM Dental Clinic AI'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')

@socketio.on('text_message')
def handle_socketio_text_message(data):
    """Handle text message via WebSocket"""
    try:
        user_message = data.get('message', '').strip()
        
        if not user_message:
            emit('error', {'message': 'Empty message'})
            return

        # Generate AI response
        ai_response = ai_assistant.generate_ai_response(user_message)
        
        # Generate audio for the response
        audio_base64 = ai_assistant.generate_audio_base64(ai_response)
        
        emit('ai_response', {
            'response': ai_response,
            'audio': audio_base64
        })
    
    except Exception as e:
        logger.error(f"Error in WebSocket text message handler: {e}")
        emit('error', {'message': 'Internal server error'})

@socketio.on('audio_data')
def handle_socketio_audio(data):
    """Handle audio data via WebSocket"""
    try:
        print("Received audio data, processing...")
        
        # Decode base64 audio data
        audio_data = base64.b64decode(data['audio'])
        print(f"Audio data size: {len(audio_data)} bytes")
        
        # Create a unique filename to avoid conflicts
        import uuid
        temp_filename = f"temp_audio_{uuid.uuid4().hex}.wav"
        tmp_file_path = os.path.join(tempfile.gettempdir(), temp_filename)
        
        # Write audio data to file
        with open(tmp_file_path, 'wb') as f:
            f.write(audio_data)
        
        print(f"Saved audio to: {tmp_file_path}")
        
        # Check if file exists and has content
        if not os.path.exists(tmp_file_path) or os.path.getsize(tmp_file_path) == 0:
            emit('error', {'message': 'Invalid audio file'})
            return
        
        # Transcribe audio
        print("Starting transcription...")
        transcribed_text = ai_assistant.transcribe_audio_file(tmp_file_path)
        print(f"Transcription result: {transcribed_text}")
        
        # Clean up immediately after transcription
        try:
            os.remove(tmp_file_path)
            print(f"Cleaned up temporary file: {tmp_file_path}")
        except Exception as cleanup_error:
            print(f"Warning: Could not delete temp file {tmp_file_path}: {cleanup_error}")
        
        if not transcribed_text or transcribed_text.strip() == "":
            emit('error', {'message': 'No speech detected in audio'})
            return

        # Emit transcribed text
        emit('transcription', {'text': transcribed_text})

        # Generate AI response
        print("Generating AI response...")
        ai_response = ai_assistant.generate_ai_response(transcribed_text)
        print(f"AI response: {ai_response}")
        
        # Generate audio for the response
        print("Generating audio response...")
        audio_base64 = ai_assistant.generate_audio_base64(ai_response)
        
        emit('ai_response', {
            'transcribed_text': transcribed_text,
            'response': ai_response,
            'audio': audio_base64
        })
        print("Response sent successfully!")
    
    except Exception as e:
        logger.error(f"Error in WebSocket audio handler: {e}")
        print(f"Detailed error: {str(e)}")
        import traceback
        traceback.print_exc()
        emit('error', {'message': f'Server error: {str(e)}'})

# Create templates directory and HTML file
def create_templates():
    """Create templates directory and HTML file"""
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RSAM Dental Clinic - AI Receptionist</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #333;
        }

        .container {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 2rem;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
            max-width: 600px;
            width: 90%;
            text-align: center;
        }

        .header {
            margin-bottom: 2rem;
        }

        .clinic-logo {
            width: 80px;
            height: 80px;
            background: linear-gradient(45deg, #4CAF50, #45a049);
            border-radius: 50%;
            margin: 0 auto 1rem;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2rem;
            color: white;
            font-weight: bold;
        }

        h1 {
            color: #2c3e50;
            margin-bottom: 0.5rem;
            font-size: 1.8rem;
        }

        .subtitle {
            color: #7f8c8d;
            font-size: 1rem;
            margin-bottom: 2rem;
        }

        .chat-container {
            background: #f8f9fa;
            border-radius: 15px;
            padding: 1.5rem;
            margin: 1.5rem 0;
            min-height: 300px;
            max-height: 400px;
            overflow-y: auto;
            border: 2px solid #e9ecef;
        }

        .message {
            margin: 1rem 0;
            padding: 0.8rem 1rem;
            border-radius: 12px;
            max-width: 80%;
            word-wrap: break-word;
            opacity: 0;
            animation: fadeIn 0.5s forwards;
        }

        .message.user {
            background: #007bff;
            color: white;
            margin-left: auto;
            text-align: right;
        }

        .message.assistant {
            background: #e9ecef;
            color: #333;
            margin-right: auto;
            text-align: left;
        }

        @keyframes fadeIn {
            to {
                opacity: 1;
            }
        }

        .controls {
            display: flex;
            gap: 1rem;
            justify-content: center;
            align-items: center;
            margin: 1.5rem 0;
        }

        .mic-button {
            width: 80px;
            height: 80px;
            border-radius: 50%;
            border: none;
            cursor: pointer;
            font-size: 2rem;
            color: white;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .mic-button.inactive {
            background: linear-gradient(45deg, #6c757d, #5a6268);
            box-shadow: 0 4px 15px rgba(108, 117, 125, 0.4);
        }

        .mic-button.listening {
            background: linear-gradient(45deg, #dc3545, #c82333);
            box-shadow: 0 4px 15px rgba(220, 53, 69, 0.4);
            animation: pulse 2s infinite;
        }

        .mic-button.processing {
            background: linear-gradient(45deg, #ffc107, #e0a800);
            box-shadow: 0 4px 15px rgba(255, 193, 7, 0.4);
        }

        @keyframes pulse {
            0% { box-shadow: 0 4px 15px rgba(220, 53, 69, 0.4); }
            50% { box-shadow: 0 4px 25px rgba(220, 53, 69, 0.8); }
            100% { box-shadow: 0 4px 15px rgba(220, 53, 69, 0.4); }
        }

        .status {
            margin: 1rem 0;
            font-weight: 500;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            transition: all 0.3s ease;
        }

        .status.inactive {
            background: #f8f9fa;
            color: #6c757d;
        }

        .status.listening {
            background: #fff5f5;
            color: #dc3545;
        }

        .status.processing {
            background: #fffdf5;
            color: #ffc107;
        }

        .text-input-container {
            margin-top: 1rem;
        }

        .text-input {
            width: 100%;
            padding: 0.8rem;
            border: 2px solid #e9ecef;
            border-radius: 10px;
            font-size: 1rem;
            margin-bottom: 0.5rem;
            transition: border-color 0.3s ease;
        }

        .text-input:focus {
            outline: none;
            border-color: #007bff;
        }

        .send-button {
            background: linear-gradient(45deg, #007bff, #0056b3);
            color: white;
            border: none;
            padding: 0.8rem 1.5rem;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1rem;
            transition: transform 0.2s ease;
        }

        .send-button:hover {
            transform: translateY(-2px);
        }

        .footer {
            margin-top: 1.5rem;
            color: #6c757d;
            font-size: 0.9rem;
        }

        .divider {
            margin: 1rem 0;
            height: 1px;
            background: #dee2e6;
        }

        .audio-player {
            margin: 0.5rem 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="clinic-logo">🦷</div>
            <h1>RSAM Dental Clinic</h1>
            <div class="subtitle">AI Receptionist - Aliya</div>
        </div>

        <div class="chat-container" id="chatContainer">
            <div class="message assistant">
                Thank you for calling the RSAM Dental Clinic. My name is Aliya, how may I help you today?
            </div>
        </div>

        <div class="controls">
            <button class="mic-button inactive" id="micButton">🎤</button>
        </div>

        <div class="status inactive" id="status">Click the microphone to start talking</div>

        <div class="divider"></div>

        <div class="text-input-container">
            <input type="text" class="text-input" id="textInput" placeholder="Or type your message here...">
            <button class="send-button" id="sendButton">Send Message</button>
        </div>

        <div class="footer">
            Powered by AI Technology | AssemblyAI • Google Gemini • ElevenLabs
        </div>
    </div>

    <script>
        class DentalReceptionistUI {
            constructor() {
                this.isListening = false;
                this.mediaRecorder = null;
                this.audioChunks = [];
                this.socket = io();
                
                this.micButton = document.getElementById('micButton');
                this.status = document.getElementById('status');
                this.chatContainer = document.getElementById('chatContainer');
                this.textInput = document.getElementById('textInput');
                this.sendButton = document.getElementById('sendButton');
                
                this.initializeEventListeners();
                this.initializeSocketListeners();
            }

            initializeEventListeners() {
                this.micButton.addEventListener('click', () => this.toggleListening());
                this.sendButton.addEventListener('click', () => this.sendTextMessage());
                this.textInput.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') {
                        this.sendTextMessage();
                    }
                });
            }

            initializeSocketListeners() {
                this.socket.on('ai_response', (data) => {
                    if (data.transcribed_text) {
                        this.addMessage(data.transcribed_text, true);
                    }
                    this.addMessage(data.response, false);
                    if (data.audio) {
                        this.playAudio(data.audio);
                    }
                    this.updateStatus('Click the microphone to start talking', 'inactive');
                    this.updateMicButton('inactive');
                });

                this.socket.on('transcription', (data) => {
                    this.addMessage(data.text, true);
                });

                this.socket.on('error', (data) => {
                    console.error('Socket error:', data.message);
                    this.updateStatus('Error: ' + data.message, 'inactive');
                    this.updateMicButton('inactive');
                });

                this.socket.on('status', (data) => {
                    console.log('Status:', data.message);
                });
            }

            addMessage(text, isUser = false) {
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${isUser ? 'user' : 'assistant'}`;
                messageDiv.textContent = text;
                
                this.chatContainer.appendChild(messageDiv);
                this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
            }

            updateStatus(message, className) {
                this.status.textContent = message;
                this.status.className = `status ${className}`;
            }

            updateMicButton(className) {
                this.micButton.className = `mic-button ${className}`;
            }

            playAudio(audioBase64) {
                const audio = new Audio(`data:audio/mpeg;base64,${audioBase64}`);
                audio.play().catch(e => console.error('Error playing audio:', e));
            }

            async toggleListening() {
                if (this.isListening) {
                    this.stopListening();
                } else {
                    await this.startListening();
                }
            }

            async startListening() {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    
                    this.mediaRecorder = new MediaRecorder(stream);
                    this.audioChunks = [];
                    
                    this.mediaRecorder.ondataavailable = (event) => {
                        this.audioChunks.push(event.data);
                    };
                    
                    this.mediaRecorder.onstop = () => {
                        this.processAudio();
                    };
                    
                    this.mediaRecorder.start();
                    this.isListening = true;
                    
                    this.updateStatus('Listening... Click again to stop', 'listening');
                    this.updateMicButton('listening');
                    
                } catch (error) {
                    console.error('Error accessing microphone:', error);
                    this.updateStatus('Error: Could not access microphone', 'inactive');
                    alert('Could not access microphone. Please ensure you have given permission.');
                }
            }

            stopListening() {
                if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
                    this.mediaRecorder.stop();
                    this.mediaRecorder.stream.getTracks().forEach(track => track.stop());
                }
                
                this.isListening = false;
                this.updateStatus('Processing your message...', 'processing');
                this.updateMicButton('processing');
            }

            async processAudio() {
                const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
                const reader = new FileReader();
                
                reader.onload = () => {
                    const base64Audio = reader.result.split(',')[1];
                    this.socket.emit('audio_data', { audio: base64Audio });
                };
                
                reader.readAsDataURL(audioBlob);
            }

            async sendTextMessage() {
                const message = this.textInput.value.trim();
                if (!message) return;
                
                this.addMessage(message, true);
                this.textInput.value = '';
                
                this.updateStatus('Processing your message...', 'processing');
                
                this.socket.emit('text_message', { message: message });
            }
        }

        // Initialize the UI when the page loads
        document.addEventListener('DOMContentLoaded', () => {
            new DentalReceptionistUI();
        });
    </script>
</body>
</html>'''
    
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)

if __name__ == "__main__":
    # Create templates directory and HTML file
    create_templates()
    
    print("🦷 RSAM Dental Clinic AI Receptionist Server Starting...")
    print("🌐 Web interface will be available at: http://localhost:5000")
    print("📱 The app supports both voice and text interactions")
    print("🔊 Make sure your speakers are on for AI voice responses")
    
    # Run the Flask app with SocketIO
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)