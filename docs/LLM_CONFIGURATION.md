# LLM Configuration Guide

> How to configure and switch between different LLM providers

**Version:** 2.0  
**Last Updated:** March 27, 2026  
**Status:** Ready

---

## 🎯 Overview

ReviewBot v2.0 supports **multiple LLM providers**. You can configure all API keys but only **one provider is active at a time**.

### Supported Providers

| Provider | Models | Best For | Cost |
|----------|--------|----------|------|
| **OpenAI** | GPT-4, GPT-3.5 | General purpose, best quality | $$$ |
| **Anthropic** | Claude 3 | Long context, safety | $$$ |
| **Google** | Gemini Pro | Multi-modal, Google integration | $$ |
| **GROQ** | Llama, Mixtral | **Fastest inference** | $ |
| **QWEN** | Qwen-72B | Alibaba Cloud, Chinese language | $$ |
| **Azure OpenAI** | GPT-4 | Enterprise, compliance | $$$ |

---

## ⚙️ Configuration

### Step 1: Set API Keys

Edit your `.env` file:

```env
# OpenAI (Default)
OPENAI_API_KEY="sk-OPENAI-DUMMY-KEY-FOR-DOCS"

# Anthropic (Claude)
ANTHROPIC_API_KEY="sk-ant-DUMMY-ANTHROPIC-KEY"

# Google (Gemini)
GOOGLE_API_KEY="GOOGLE-DUMMY-KEY-FOR-DOCS"

# GROQ (Fast LLM)
GROQ_API_KEY="gsk_GROQ-DUMMY-KEY-FOR-DOCS"

# QWEN (Alibaba)
QWEN_API_KEY="QWEN-DUMMY-KEY-FOR-DOCS"

# Azure OpenAI
AZURE_OPENAI_API_KEY="AZURE-DUMMY-KEY-FOR-DOCS"
AZURE_OPENAI_ENDPOINT="https://DUMMY-RESOURCE.openai.azure.com/"
AZURE_OPENAI_DEPLOYMENT="DUMMY-DEPLOYMENT"
```

---

### Step 2: Choose Active Provider

Set which provider to use:

```env
# Choose one: openai, anthropic, google, groq, qwen, azure
ACTIVE_LLM_PROVIDER="openai"
```

**That's it!** ReviewBot will use the selected provider.

---

## 🔄 Switching Providers

### Example 1: Switch to GROQ (Fast & Cheap)

```env
ACTIVE_LLM_PROVIDER="groq"
GROQ_API_KEY="gsk_your-groq-key-here"
```

**Benefits:**
- ⚡ Fastest inference (10x faster than OpenAI)
- 💰 Cheaper than OpenAI
- 🎯 Good for development/testing

**Trade-offs:**
- Slightly lower quality than GPT-4
- Limited model selection

---

### Example 2: Switch to Claude (Long Context)

```env
ACTIVE_LLM_PROVIDER="anthropic"
ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

**Benefits:**
- 📚 200K context window
- 🛡️ Better safety/alignment
- 📝 Excellent for long documents

**Trade-offs:**
- Slower than GROQ
- More expensive

---

### Example 3: Switch to QWEN (Alibaba Cloud)

```env
ACTIVE_LLM_PROVIDER="qwen"
QWEN_API_KEY="your-qwen-key-here"
```

**Benefits:**
- 🇨🇳 Excellent for Chinese language
- ☁️ Alibaba Cloud integration
- 💼 Enterprise support

**Trade-offs:**
- Requires Alibaba Cloud account
- Documentation mostly in Chinese

---

## 🔒 Security Configuration Explained

### Why These Settings?

```env
# Security Configuration
SECRET_KEY="your-secret-key-here"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### SECRET_KEY

**What it does:**
- Used to sign JWT (JSON Web Tokens)
- Ensures tokens can't be forged
- Protects API endpoints from unauthorized access

**Why required:**
- Without it, anyone could access your API
- Prevents token tampering
- Industry standard for authentication

**How to generate:**

**Python:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**PowerShell:**
```powershell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
```

**Linux:**
```bash
openssl rand -hex 32
```

**⚠️ IMPORTANT:**
- Keep this SECRET_KEY secret!
- Never commit to Git
- Change in production
- Use environment variables or secrets manager

---

### ALGORITHM

**What it does:**
- Specifies the algorithm used to sign JWT tokens
- HS256 = HMAC with SHA-256

**Why HS256:**
- Industry standard
- Fast and secure
- Widely supported
- Symmetric (same key for signing and verification)

**Alternatives:**
- RS256 (asymmetric, more secure but slower)
- ES256 (ECDSA, good for mobile)

**Default:** HS256 (recommended for most cases)

---

### ACCESS_TOKEN_EXPIRE_MINUTES

**What it does:**
- How long JWT tokens remain valid
- After expiration, user must login again

**Why 30 minutes:**
- Balance between security and convenience
- Short enough to limit damage if token stolen
- Long enough for normal usage

**Adjust based on needs:**
```env
# High security (15 minutes)
ACCESS_TOKEN_EXPIRE_MINUTES=15

# Standard (30 minutes)
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Convenient (60 minutes)
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Development (24 hours)
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

---

## 🎯 Provider Comparison

### Performance Comparison

| Provider | Speed | Quality | Cost | Best For |
|----------|-------|---------|------|----------|
| **GROQ** | ⚡⚡⚡⚡⚡ | ⭐⭐⭐⭐ | $ | Development, testing |
| **OpenAI** | ⚡⚡⚡⚡ | ⭐⭐⭐⭐⭐ | $$$ | Production, best quality |
| **Anthropic** | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | $$$ | Long documents |
| **Google** | ⚡⚡⚡⚡ | ⭐⭐⭐⭐ | $$ | Multi-modal |
| **QWEN** | ⚡⚡⚡ | ⭐⭐⭐⭐ | $$ | Chinese language |
| **Azure** | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | $$$ | Enterprise |

---

### Cost Comparison (per 1M tokens)

| Provider | Input | Output | Speed |
|----------|-------|--------|-------|
| **GROQ** | $0.50 | $0.80 | Fastest |
| **OpenAI GPT-4** | $30 | $60 | Fast |
| **Anthropic Claude** | $25 | $75 | Medium |
| **Google Gemini** | $7 | $21 | Fast |
| **QWEN** | $10 | $40 | Medium |
| **Azure GPT-4** | $30 | $60 | Fast |

*Prices approximate, check provider websites for current pricing*

---

## 🚀 Quick Start Examples

### Example 1: Development with GROQ

```bash
# Copy environment template
copy .env.docker .env

# Edit .env
notepad .env

# Set GROQ as active provider
ACTIVE_LLM_PROVIDER="groq"
GROQ_API_KEY="gsk_your-groq-key-here"

# Start Docker
docker-compose up -d
```

**Why GROQ for development:**
- Fast feedback loop
- Cheap for testing
- Good enough quality for development

---

### Example 2: Production with OpenAI

```bash
# Edit .env
notepad .env

# Set OpenAI as active provider
ACTIVE_LLM_PROVIDER="openai"
OPENAI_API_KEY="sk-your-production-key-here"

# Increase security
ACCESS_TOKEN_EXPIRE_MINUTES=15

# Start Docker
docker-compose --profile production up -d --build
```

**Why OpenAI for production:**
- Best quality
- Most reliable
- Enterprise support available

---

### Example 3: Multi-Region with Azure

```bash
# Edit .env
notepad .env

# Set Azure as active provider
ACTIVE_LLM_PROVIDER="azure"
AZURE_OPENAI_API_KEY="your-azure-key"
AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
AZURE_OPENAI_DEPLOYMENT="gpt-4"

# Start Docker
docker-compose up -d
```

**Why Azure for enterprise:**
- Compliance (HIPAA, SOC2)
- Private networking
- SLA guarantees
- Enterprise support

---

## 🔧 Troubleshooting

### Issue: "No API key configured"

```
Error: No API key found for active provider: groq
```

**Solution:**
```env
# Make sure you set the correct API key
GROQ_API_KEY="gsk_your-key-here"

# And set active provider
ACTIVE_LLM_PROVIDER="groq"
```

---

### Issue: "Invalid API key"

```
Error: Invalid API key for provider: openai
```

**Solution:**
1. Check API key is correct (no typos)
2. Verify API key is active (not expired)
3. Check API key has correct permissions
4. Restart Docker container

---

### Issue: "Provider not supported"

```
Error: Unknown provider: mistral
```

**Solution:**
```env
# Use only supported providers:
ACTIVE_LLM_PROVIDER="openai"     # ✓
ACTIVE_LLM_PROVIDER="anthropic"  # ✓
ACTIVE_LLM_PROVIDER="google"     # ✓
ACTIVE_LLM_PROVIDER="groq"       # ✓
ACTIVE_LLM_PROVIDER="qwen"       # ✓
ACTIVE_LLM_PROVIDER="azure"      # ✓
```

---

## 📊 Monitoring Usage

### Check Which Provider is Active

```bash
# Check environment variable
docker-compose exec app env | grep ACTIVE_LLM_PROVIDER

# Check in application
curl http://localhost:8000/health
# Response includes active provider
```

### Track Token Usage

Each provider has different dashboards:

- **OpenAI:** https://platform.openai.com/usage
- **Anthropic:** https://console.anthropic.com/settings/keys
- **Google:** https://console.cloud.google.com/apis/credentials
- **GROQ:** https://console.groq.com/usage
- **QWEN:** https://dashscope.console.aliyun.com/
- **Azure:** https://portal.azure.com/#view/Microsoft_Azure_Billing/

---

## 🎯 Best Practices

### 1. Development

```env
ACTIVE_LLM_PROVIDER="groq"
GROQ_API_KEY="gsk_dev-key-here"
ACCESS_TOKEN_EXPIRE_MINUTES=60  # Longer for dev
```

**Why:**
- Fast iteration
- Low cost
- Good enough quality

---

### 2. Testing

```env
ACTIVE_LLM_PROVIDER="openai"
OPENAI_API_KEY=sk-OPENAI-DUMMY-KEY-FOR-DOCS              # Required
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**Why:**
- Match production provider
- Catch provider-specific issues
- Accurate performance testing

---

### 3. Production

```env
ACTIVE_LLM_PROVIDER="openai"  # or azure for enterprise
OPENAI_API_KEY="sk-prod-key-here"
ACCESS_TOKEN_EXPIRE_MINUTES=15  # Shorter for security
SECRET_KEY="production-secret-key-change-this"
```

**Why:**
- Best quality
- Maximum security
- Enterprise support

---

## 🔗 Related Documents

- [DOCKER_GUIDE.md](DOCKER_GUIDE.md) - Docker setup
- [requirements.md](requirements.md) - Full requirements
- [DESIGN_PHASE_KICKOFF.md](DESIGN_PHASE_KICKOFF.md) - Implementation plan

---

*Document Owner: Engineering Team*  
*Last Updated: March 27, 2026*  
*Next Review: After Phase 1 completion*
