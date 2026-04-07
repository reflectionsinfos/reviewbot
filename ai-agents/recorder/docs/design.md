🧠 System Architecture

🔷 Core Components

    Capture Layer
        OBS / Virtual Audio
        Teams Bot (future)

    Processing Layer
        FFmpeg (audio extraction)
        Whisper (transcription)
        Diarization service

    Intelligence Layer
        Chunking service
        Embedding generator
        Vector DB (RAG)

    LLM Agent Layer
        Query understanding
        Context retrieval
        Response generation

    Application Layer
        Chat UI
        REST APIs

🧩 Component Design

🎤 Capture Service
    Handles:
        Audio stream capture
        File storage

    Outputs:
        .wav file

🧾 Transcription Service
    Input: audio file
    Output:
        {
            "segments": [
            {"start": 0, "end": 5, "text": "..."}
        ]
    }

🧠 Chunking Service
    Splits transcript into chunks
    Adds overlap
    Stores embeddings

🔍 Retrieval Service (RAG)
    Query → embedding
    Retrieve top-k relevant chunks

🤖 LLM Agent
    Responsibilities:
        Context merging
        Reasoning
        Answer generation

    Input:
        User query
        Transcript chunks
        Project knowledge

💬 Chat Service
    Maintains session context
    Sends query to LLM agent
    Displays response


🧱 Data Flow
    Audio → Whisper → Transcript → Chunk → Embed → Vector DB
                                      ↓
    User Query → Retrieve Context → LLM → Response


🧑‍💻 Teams Bot Design
    Components:
        Bot Service (Azure)
        Graph API listener
        Recording trigger

    Flow:
        Join Meeting → Capture → Upload → Process → Post Summary

🔐 Security
    Token-based authentication
    Secure storage (encrypted)
    API rate limiting

📈 Scalability
    Microservices architecture
    Async processing (Celery / Kafka)
    Horizontal scaling    

⚡ Performance Optimizations
    Use Faster-Whisper (GPU)
    Cache embeddings
    Incremental transcription