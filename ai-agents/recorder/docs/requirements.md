🧭 Objective

Build an LLM-powered Meeting Intelligence System that:

    Captures meeting audio/video
    Generates detailed transcripts
    Applies reasoning using project + domain knowledge
    Enables interactive chat over meeting content
    Supports both:
        Local Agent (real-time + UI)
        Bot Participant (Teams-based automation)


🧩 System Variants

1️⃣ Local Agent (Primary MVP)

    A locally running Python/Node app that:

    Captures system audio
    Transcribes in near real-time or post-meeting
    Provides a chat UI
    Connects to LLM for reasoning

2️⃣ Teams Bot Account (Automation Layer)

    Joins meetings automatically
    Records meeting
    Generates transcript + insights
    Posts output to Teams channel
    Creates discussion thread


🧱 Functional Requirements
    
    🎤 Audio/Video Capture
        
    Capture system audio (Teams/Zoom/etc.)
    Optional mic capture (user voice)
    Store recordings (mp4/mkv)

🧾 Transcription
    Full detailed transcription (not summary)
    Timestamped segments
    Optional speaker diarization

🧠 LLM Reasoning
    Generate:
        Detailed summaries
        Decisions
        Action items
        Risks
    Answer user queries via chat

💬 Chat Interface
    
    Ask questions like:
        “What decisions were made?”
        “What are the risks?”
    Context-aware answers using transcript + knowledge


🗂 Knowledge Integration (RAG)
    Integrate:
        Project docs
        Code summaries
        Domain knowledge
    Use vector DB for retrieval


🧑‍💻 Teams Bot Features
    Auto-join meeting
    Record session
    Upload transcript
    
    Create:
        Summary message
        Dedicated discussion thread/channel

⚙️ Non-Functional Requirements
    
    Low latency (for local agent)
    High transcription accuracy
    Scalable (cloud-ready)
    Secure (no data leaks)
    Modular architecture

🏗️ Tech Stack

    🟢 Backend
        Python (FastAPI) → transcription + AI
        Node.js (optional) → UI backend / orchestration

    🟢 Frontend
        React / Next.js (lightweight UI)
        Electron (for desktop app)
    
    🟢 AI / ML
        Whisper / Faster-Whisper → transcription
        WhisperX / pyannote → diarization
        OpenAI / Llama / Mixtral → LLM

    🟢 Audio Processing
        FFmpeg → audio extraction
        Virtual Audio Cable → system audio capture

    🟢 Storage
        PostgreSQL → metadata
        S3 / Local FS → recordings
        Vector DB:
            FAISS (local)
            Pinecone / Weaviate (cloud)
    🟢 Integration
        Microsoft Graph API → Teams bot
        Azure Bot Service       

🔄 High-Level Flow

Local Agent
    Audio Capture → Whisper → Transcript → Chunk → Embed → Vector DB → LLM → UI Chat

Teams Bot
    Meeting Join → Record → Process → Transcript → LLM → Post to Teams   

🚀 Approach Strategy
    Phase 1 (MVP)
        Local agent
        Post-meeting transcription
        Chat UI

    Phase 2
        Speaker diarization
        Knowledge integration (RAG)

    Phase 3
        Teams bot integration
        Auto workflows

    Phase 4
        Real-time streaming AI agent