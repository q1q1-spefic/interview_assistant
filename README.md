# 🎯 AI Interview Assistant (即答侠 / HireMeAI)

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-orange.svg)](https://openai.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> 🚀 **Real-time AI-powered interview preparation system** with voice recognition, mock interviews, and personalized question generation.

---

## ✨ Key Features

### 📄 Resume Intelligence
- **AI Resume Parser** - GPT-4 powered resume analysis (PDF/DOCX/TXT)
- **Smart Optimization** - AI-driven resume improvement suggestions
- **Version Control** - Track and compare resume versions
- **Entity Extraction** - Extract skills, experience, and education

### 🎯 Job Matching
- **JD Analysis** - Automatic job description parsing from URLs or text
- **Skill Gap Detection** - Identify missing skills and experience
- **Match Scoring** - Resume-JD compatibility scoring

### 💡 Interview Preparation
- **Personalized Questions** - AI-generated questions based on your resume and JD
- **STAR Framework** - Behavioral questions with STAR/PREP structure
- **Template Library** - ChromaDB-powered semantic search for 1000+ questions
- **Difficulty Levels** - Questions categorized by difficulty

### 🎤 Voice & Mock Interviews
- **Real-time Mock Interviews** - Practice with AI interviewer
- **Voice Recognition** - Azure Speech Services integration
- **Speaker Diarization** - Picovoice Eagle speaker recognition
- **AI Feedback** - Instant analysis and improvement suggestions
- **WebSocket Streaming** - Low-latency real-time conversations

### 🧠 Memory & Context
- **Graph-based Memory** - Persistent user context across sessions
- **Vector Search** - Semantic similarity for template matching
- **Intelligent Deduplication** - Smart template and question merging

### 💳 Premium Features
- **Payment System** - Subscription and one-time payment support
- **Referral Program** - Reward system for user referrals
- **Device Fingerprinting** - Fraud prevention

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API Key
- Azure Speech Services Key (optional, for voice features)
- Picovoice Access Key (optional, for speaker recognition)

### Installation

```bash
# Clone the repository
git clone https://github.com/q1q1-spefic/interview_assistant.git
cd interview_assistant

# Run setup script
chmod +x setup.sh
./setup.sh

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Running the Application

```bash
# Start the server
python interview_assistant_system.py

# Or use the start script
./start.sh

# Access at http://localhost:5001
```

---

## 🏗️ Architecture

```
interview_assistant/
├── interview_assistant_system.py  # Main Flask application (11k+ lines)
├── config.py                      # System configuration
│
├── Resume Processing
│   ├── enhanced_resume_parser.py
│   ├── resume_optimizer.py
│   └── resume_analysis_service.py
│
├── JD & Entity Extraction
│   ├── advanced_jd_analyzer.py
│   └── advanced_entity_extractor.py
│
├── Interview Templates
│   ├── template_deduplicator.py
│   ├── enhanced_star_optimizer.py
│   └── interview_template_matcher.py
│
├── Voice & Mock Interviews
│   ├── voice_interview_assistant.py
│   ├── eagle_speaker_recognition.py
│   ├── advanced_mock_interview_manager.py
│   └── realtime_mock_interview_engine.py
│
├── Memory & Vector Search
│   ├── memory_graph_manager.py
│   ├── enhanced_memory_graph_manager.py
│   └── vector_similarity_detector.py
│
├── User Management
│   ├── user_auth.py
│   ├── payment_system.py
│   └── referral_tracker.py
│
└── templates/                     # Jinja2 HTML templates
```

---

## 💻 Tech Stack

- **Backend**: Flask, SQLite, ChromaDB
- **AI**: OpenAI GPT-4, GPT-4o-mini
- **Voice**: Azure Speech Services, Picovoice Eagle
- **Vector DB**: ChromaDB (embeddings search)
- **Frontend**: Jinja2, vanilla JavaScript
- **Real-time**: WebSocket, Server-Sent Events (SSE)

---

## 📊 Performance Metrics

- **Resume Parsing**: ~5s (PDF/DOCX → Structured JSON)
- **Question Generation**: ~3s (50 personalized questions)
- **First-byte Latency**: ~1.0s (real-time mock interview)
- **Speaker Recognition**: 95% accuracy (Picovoice Eagle)
- **Template Search**: <100ms (ChromaDB vector similarity)

---

## 🔧 Configuration

Edit `.env` with your API keys:

```bash
OPENAI_API_KEY=your_openai_key
AZURE_SPEECH_KEY=your_azure_key
AZURE_SPEECH_REGION=eastus
PICOVOICE_ACCESS_KEY=your_picovoice_key  # Optional
```

See `config.py` for advanced configuration options.

---

## 📖 Documentation

- [Technical Documentation](CLAUDE.md)
- [Real-time Mock Interview Integration](REALTIME_MOCK_INTERVIEW_INTEGRATION.md)
- [Marketing Brief](MarketingBrief.md)

---

## 🧪 Testing

```bash
# Run tests
python test_speaker_recognition.py
python resume_analysis_test.py
python test_eagle.py
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- OpenAI for GPT-4 API
- Microsoft Azure for Speech Services
- Picovoice for Eagle Speaker Recognition
- ChromaDB for vector similarity search

---

## 📞 Contact

- Website: [interviewasssistant.com](https://interviewasssistant.com)
- GitHub: [@q1q1-spefic](https://github.com/q1q1-spefic)

---

**⭐ Star this repo if you find it helpful!**
