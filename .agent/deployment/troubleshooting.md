# Troubleshooting Guide

## Common Issues and Solutions

---

## Installation Issues

### Issue: Dependencies Installation Fails

**Error:**
```
ERROR: Could not find a version that satisfies the requirement langchain==0.1.9
```

**Solutions:**

1. **Upgrade pip:**
   ```bash
   python -m pip install --upgrade pip
   ```

2. **Clear pip cache:**
   ```bash
   pip cache purge
   pip install -r requirements.txt
   ```

3. **Install wheel first:**
   ```bash
   pip install wheel
   pip install -r requirements.txt
   ```

4. **Use specific Python version:**
   ```bash
   # Recommended: Python 3.10 or 3.11
   python --version
   ```

---

### Issue: Virtual Environment Problems

**Error:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Solutions:**

1. **Activate virtual environment:**
   ```bash
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

2. **Verify activation:**
   ```bash
   # Should show venv path
   which python  # Linux/Mac
   where python  # Windows
   ```

3. **Reinstall in venv:**
   ```bash
   pip install -r requirements.txt --force-reinstall
   ```

---

## Database Issues

### Issue: Database Not Found

**Error:**
```
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) unable to open database file
```

**Solutions:**

1. **Run setup script:**
   ```bash
   python setup.py
   ```

2. **Manually create database:**
   ```bash
   python -c "from app.db.session import init_db; import asyncio; asyncio.run(init_db())"
   ```

3. **Check file permissions:**
   ```bash
   # Linux/Mac
   ls -la reviews.db
   chmod 644 reviews.db
   
   # Windows
   icacls reviews.db /grant Everyone:F
   ```

4. **Verify DATABASE_URL in .env:**
   ```env
   DATABASE_URL="sqlite+aiosqlite:///./reviews.db"
   ```

---

### Issue: Database Locked

**Error:**
```
sqlite3.OperationalError: database is locked
```

**Solutions:**

1. **Close other connections:**
   - Close any open database browsers
   - Stop other running instances

2. **Increase timeout:**
   ```python
   engine = create_async_engine(
       settings.DATABASE_URL,
       connect_args={"timeout": 60}
   )
   ```

3. **Delete and recreate (dev only):**
   ```bash
   rm reviews.db
   python setup.py
   ```

---

## API Issues

### Issue: Server Won't Start

**Error:**
```
ImportError: No module named 'uvicorn'
```

**Solution:**
```bash
pip install -r requirements.txt
```

---

**Error:**
```
Address already in use
```

**Solutions:**

1. **Find and kill process:**
   ```bash
   # Windows
   netstat -ano | findstr :8000
   taskkill /PID <PID> /F
   
   # Linux/Mac
   lsof -i :8000
   kill -9 <PID>
   ```

2. **Use different port:**
   ```bash
   uvicorn main:app --port 8001
   ```

---

### Issue: CORS Errors

**Error:**
```
Access to XMLHttpRequest has been blocked by CORS policy
```

**Solutions:**

1. **Update CORS settings in main.py:**
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:3000"],  # Your frontend URL
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

2. **For development, allow all (not for production):**
   ```python
   allow_origins=["*"]
   ```

---

## Authentication Issues

### Issue: Invalid Token

**Error:**
```
401 Unauthorized: Could not validate credentials
```

**Solutions:**

1. **Check token format:**
   ```bash
   # Correct format
   Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

2. **Token expired:**
   - Default expiration: 30 minutes
   - Login again to get new token

3. **Wrong SECRET_KEY:**
   ```env
   # Ensure same SECRET_KEY in .env
   SECRET_KEY=your-secret-key
   ```

---

### Issue: Can't Login

**Error:**
```
401 Unauthorized: Incorrect email or password
```

**Solutions:**

1. **Verify credentials:**
   - Default demo user: `admin@example.com` / `admin123`

2. **Check password hash:**
   ```python
   from passlib.context import CryptContext
   pwd_context = CryptContext(schemes=["bcrypt"])
   print(pwd_context.verify("admin123", hashed_password))
   ```

3. **Create new user:**
   ```bash
   curl -X POST "http://localhost:8000/api/auth/register" \
     -d "email=test@example.com" \
     -d "password=test123" \
     -d "full_name=Test User"
   ```

---

## OpenAI API Issues

### Issue: Authentication Error

**Error:**
```
openai.AuthenticationError: Error code: 401 - Invalid API key
```

**Solutions:**

1. **Verify API key:**
   ```bash
   # Test key
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer $OPENAI_API_KEY"
   ```

2. **Check .env file:**
   ```env
   OPENAI_API_KEY=sk-...  # No quotes, no extra spaces
   ```

3. **Restart server after changing .env:**
   ```bash
   # Stop server (Ctrl+C)
   uvicorn main:app --reload
   ```

4. **Check API key credits:**
   - Visit: https://platform.openai.com/account/usage

---

### Issue: Rate Limit Exceeded

**Error:**
```
openai.RateLimitError: Rate limit reached
```

**Solutions:**

1. **Wait and retry:**
   - Default limits: 3 requests/minute (GPT-4)

2. **Implement retry logic:**
   ```python
   from tenacity import retry, stop_after_attempt, wait_exponential
   
   @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
   async def call_openai():
       ...
   ```

3. **Upgrade OpenAI plan:**
   - Visit: https://platform.openai.com/account/billing/overview

---

## Voice Issues

### Issue: Speech-to-Text Fails

**Error:**
```
STT Error: Could not transcribe audio
```

**Solutions:**

1. **Check audio format:**
   - Supported: WAV, MP3, M4A, WebM, FLAC
   - Recommended: WAV, 16-bit, 16kHz

2. **Check file size:**
   - Maximum: 25 MB
   - Compress if larger

3. **Verify OpenAI API access:**
   ```bash
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer $OPENAI_API_KEY"
   ```

4. **Test with sample audio:**
   ```bash
   # Create test audio (Linux/Mac)
   say -o test.wav "Hello, this is a test"
   ```

---

### Issue: Text-to-Speech Fails

**Error:**
```
TTS Error: Audio generation failed
```

**Solutions:**

1. **Check API key has TTS access:**
   - Some older keys may need upgrade

2. **Verify voice name:**
   ```python
   # Valid voices: alloy, echo, fable, onyx, nova, shimmer
   voice = "alloy"
   ```

3. **Check output directory:**
   ```bash
   mkdir -p uploads/voice
   chmod 755 uploads/voice
   ```

---

## Report Generation Issues

### Issue: PDF Generation Fails

**Error:**
```
ImportError: No module named 'reportlab'
```

**Solution:**
```bash
pip install reportlab
```

---

**Error:**
```
PermissionError: [Errno 13] Permission denied: './reports/report.pdf'
```

**Solution:**
```bash
# Create directory with proper permissions
mkdir -p reports
chmod 755 reports
```

---

### Issue: Markdown Report Empty

**Error:**
Report file created but empty

**Solutions:**

1. **Check report_data:**
   ```python
   print(state["report_data"])  # Should not be None
   ```

2. **Verify encoding:**
   ```python
   with open(file_path, 'w', encoding='utf-8') as f:
       f.write(md_content)
   ```

---

## Performance Issues

### Issue: Slow API Responses

**Symptoms:**
- API calls taking > 5 seconds
- Database queries slow

**Solutions:**

1. **Enable query logging:**
   ```python
   engine = create_async_engine(
       settings.DATABASE_URL,
       echo=True  # Log queries
   )
   ```

2. **Add database indexes:**
   ```python
   class Project(Base):
       id = Column(Integer, primary_key=True, index=True)
       email = Column(String, unique=True, index=True)
   ```

3. **Use connection pooling:**
   ```python
   engine = create_async_engine(
       DATABASE_URL,
       pool_size=10,
       max_overflow=20
   )
   ```

4. **Cache frequently accessed data:**
   ```python
   from functools import lru_cache
   
   @lru_cache(maxsize=128)
   def get_checklist_items(checklist_id):
       ...
   ```

---

### Issue: High Memory Usage

**Symptoms:**
- Memory usage grows over time
- Application slows down

**Solutions:**

1. **Limit conversation history:**
   ```python
   # Keep only last 10 messages
   state["conversation_history"] = state["conversation_history"][-10:]
   ```

2. **Stream large responses:**
   ```python
   from fastapi.responses import StreamingResponse
   ```

3. **Profile memory usage:**
   ```bash
   pip install memory-profiler
   python -m memory_profiler main.py
   ```

---

## File Upload Issues

### Issue: File Upload Fails

**Error:**
```
FileNotFoundError: [Errno 2] No such file or directory
```

**Solutions:**

1. **Create upload directory:**
   ```bash
   mkdir -p uploads
   chmod 755 uploads
   ```

2. **Check file size limits:**
   ```python
   # In main.py or config
   MAX_UPLOAD_SIZE = 25 * 1024 * 1024  # 25 MB
   ```

3. **Verify temp directory:**
   ```bash
   # Ensure /tmp exists and is writable
   ls -la /tmp
   ```

---

## Checklist Parsing Issues

### Issue: Excel File Not Parsed

**Error:**
```
ValueError: Delivery Check List sheet not found
```

**Solutions:**

1. **Verify sheet names:**
   - Must be exactly: "Delivery Check List V 1.0" and "Technical Check List V 1.0"

2. **Check Excel format:**
   - Must be .xlsx (not .xls)
   - Not password protected

3. **Inspect file:**
   ```python
   import pandas as pd
   xl = pd.ExcelFile("file.xlsx")
   print(xl.sheet_names)  # Check sheet names
   ```

---

## Deployment Issues

### Issue: Production Deployment Fails

**Error:**
```
ModuleNotFoundError: No module named 'app'
```

**Solutions:**

1. **Set PYTHONPATH:**
   ```bash
   export PYTHONPATH=/path/to/app:$PYTHONPATH
   ```

2. **Install as package:**
   ```bash
   pip install -e .
   ```

3. **Use absolute imports:**
   ```python
   # Correct
   from app.core.config import settings
   
   # Incorrect
   from core.config import settings
   ```

---

### Issue: Environment Variables Not Loaded

**Error:**
```
Settings error: OPENAI_API_KEY not found
```

**Solutions:**

1. **Verify .env location:**
   ```bash
   # Should be in project root
   ls -la .env
   ```

2. **Check .env format:**
   ```env
   # Correct
   OPENAI_API_KEY=sk-...
   
   # Incorrect (quotes)
   OPENAI_API_KEY="sk-..."
   ```

3. **Load manually:**
   ```python
   from dotenv import load_dotenv
   load_dotenv()
   ```

---

## Debugging Tips

### Enable Debug Logging

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.debug("Debug message")
```

### Test Endpoints

```bash
# Health check
curl http://localhost:8000/health

# API docs
curl http://localhost:8000/docs

# Test endpoint
curl http://localhost:8000/api/projects/
```

### Database Inspection

```bash
# SQLite CLI
sqlite3 reviews.db

# List tables
.tables

# Query data
SELECT * FROM projects;
```

---

## Getting Help

1. **Check logs:**
   ```bash
   # Application logs
   tail -f logs/app.log
   
   # Server logs
   journalctl -u your-service -f
   ```

2. **Enable verbose mode:**
   ```bash
   uvicorn main:app --log-level debug
   ```

3. **Check GitHub Issues:**
   - Search for similar issues
   - Create new issue with details

4. **Contact support:**
   - Email: support@example.com
   - Slack: #ai-review-agent

---

*Last Updated: 2026-03-25*
