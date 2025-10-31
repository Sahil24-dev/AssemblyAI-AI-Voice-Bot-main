# AI Dental Assistant Web Application

A complete web-based AI dental receptionist using AssemblyAI for speech-to-text, Google Gemini for AI responses, and ElevenLabs for text-to-speech.

## 🚀 Features

- **Real-time Speech Recognition** - Using AssemblyAI's streaming API
- **AI Conversation** - Powered by Google Gemini AI
- **Natural Voice Synthesis** - ElevenLabs voice generation
- **Dual Mode Support** - Both voice and text input options
- **Modern Web Interface** - React-based responsive UI
- **Real-time Communication** - WebSocket integration for instant responses

## 📋 Requirements

### Backend Requirements (`requirements.txt`)
```
flask==2.3.3
flask-cors==4.0.0
flask-socketio==5.3.6
assemblyai==0.17.0
google-generativeai==0.3.2
elevenlabs==0.2.26
python-socketio==5.9.0
eventlet==0.33.3
```

### API Keys Required
- **AssemblyAI API Key** - Get from [AssemblyAI](https://www.assemblyai.com/)
- **Google Gemini API Key** - Get from [Google AI Studio](https://aistudio.google.com/)
- **ElevenLabs API Key** - Get from [ElevenLabs](https://elevenlabs.io/)

## 🛠️ Installation & Setup

### 1. Clone and Install Dependencies

```bash
# Create project directory
mkdir dental-assistant-web
cd dental-assistant-web

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Update the API keys in `app.py`:

```python
# ==============================
# API KEYS - REPLACE WITH YOUR KEYS
# ==============================
ASSEMBLY_KEY = "your_assemblyai_key_here"
GEMINI_KEY = "your_gemini_key_here"
ELEVEN_KEY = "your_elevenlabs_key_here"
```

### 3. Run the Application

**Backend (Terminal 1):**
```bash
python app.py
```
The Flask server will start on `http://localhost:5000`

**Frontend:**
The React UI is embedded and served through the web interface. Just open your browser to `http://localhost:5000` or use the React component in your preferred React environment.

## 🎯 Usage Guide

### Voice Mode (Default)
1. Click **"Start Session"** to initialize the AI assistant
2. Grant microphone permissions when prompted
3. Click **"Start Recording"** to begin speaking
4. Speak your question or request
5. Click **"Stop Recording"** when finished
6. The AI will process your speech and respond with both text and voice

### Text Mode
1. Enable the **"Text Mode"** checkbox
2. Click **"Start Session"**
3. Type your message in the input field
4. Press **Enter** or click the **Send** button
5. The AI will respond with text and voice

## 🔧 Customization

### Modify AI Behavior
Edit the system prompt in `app.py`:
```python
self.full_transcript = [
    {"role": "system", "content": "You are a receptionist at a dental clinic. Be resourceful and efficient."}
]
```

### Change Voice Settings
Modify the ElevenLabs voice in the `generate_audio` method:
```python
audio_stream = generate(
    api_key=ELEVEN_KEY,
    text=text,
    voice="Rachel",  # Change to different voice
    stream=False,
)
```

### Adjust Audio Quality
Modify the sample rate and recording parameters:
```python
StreamingParameters(
    sample_rate=16000,  # Adjust sample rate
    format_turns=True,
)
```

## 🏗️ Architecture

### Backend Components
- **Flask Server** - Main web server and API endpoints
- **SocketIO** - Real-time bidirectional communication
- **WebAI_Assistant Class** - Core AI logic and API integrations
- **AssemblyAI Streaming** - Real-time speech-to-text
- **Google Gemini** - AI conversation generation
- **ElevenLabs** - Text-to-speech synthesis

### Frontend Components
- **React UI** - Modern responsive interface
- **WebSocket Client** - Real-time server communication
- **Audio Recording** - Browser microphone access
- **Audio Playback** - AI response audio playback
- **Text Input** - Alternative text-based interaction

## 🚨 Troubleshooting

### Common Issues

**1. Microphone Access Denied**
- Enable microphone permissions in browser settings
- Use HTTPS for production deployment
- Try the text mode as an alternative

**2. WebSocket Connection Failed**
- Ensure Flask server is running on port 5000
- Check firewall settings
- Verify CORS configuration

**3. API Key Errors**
- Verify all API keys are correct and active
- Check API usage limits and billing
- Ensure keys have necessary permissions

**4. Audio Playback Issues**
- Check browser audio permissions
- Verify ElevenLabs API key and credits
- Fallback to Web Speech API if ElevenLabs fails

### Performance Optimization

**For Better Real-time Performance:**
- Use WebRTC for audio streaming
- Implement audio buffering
- Add connection quality indicators
- Optimize chunk sizes for your network

**For Production Deployment:**
- Use HTTPS/WSS for secure connections
- Implement proper error handling and retry logic
- Add user authentication and session management
- Monitor API usage and costs

## 📝 API Endpoints

### REST Endpoints
- `GET /api/health` - Health check
- `POST /api/text-to-speech` - Convert text to speech

### WebSocket Events
**Client to Server:**
- `start_session` - Initialize AI session
- `end_session` - Terminate session
- `audio_chunk` - Send audio data
- `text_input` - Send text message

**Server to Client:**
- `connected` - Connection established
- `session_status` - Session state updates
- `transcript_received` - Speech transcription
- `ai_response` - AI text response
- `audio_response` - AI voice response
- `error` - Error messages

## 🔐 Security Considerations

- Store API keys in environment variables for production
- Implement rate limiting for API calls
- Add user authentication for production use
- Validate and sanitize all user inputs
- Use HTTPS/WSS in production environments

## 📊 Monitoring & Analytics

Consider adding:
- Conversation logging and analytics
- API usage monitoring
- Performance metrics
- Error tracking and alerting
- User interaction analytics

## 🤝 Contributing

Feel free to contribute by:
- Reporting bugs and issues
- Suggesting new features
- Improving documentation
- Submitting pull requests

## 📄 License

This project is provided as-is for educational and development purposes. Please ensure compliance with all API providers' terms of service.

---

**Happy coding! 🎉**