# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI Interview Assistant System - A Flask-based web application that helps users prepare for job interviews through resume analysis, job description matching, personalized interview question generation, and mock interview sessions with voice recognition capabilities.

## Commands

### Development Setup
```bash
# Initial setup
./setup.sh

# Start the application
python interview_assistant_system.py
# Or using the start script (production path)
./start.sh

# Access at http://localhost:5001
```

### Dependencies
```bash
# Install all dependencies
pip install -r requirements.txt

# Install minimal dependencies
pip install -r requirements_minimal.txt
```

### Database Operations
The system uses SQLite databases stored in `data/`:
- `users.db` - User accounts and authentication
- `templates.db` - Interview question templates
- `mock_interviews.db` - Mock interview sessions
- `referrals.db` - Referral tracking
- `speaker_profiles.db` - Voice recognition profiles

## Architecture

### Core System (`interview_assistant_system.py`)
The main Flask application (11,632 lines) integrates all components:

**Key Classes:**
- `ResumeParser` (line 561) - Parses PDF/DOCX/TXT resumes using OpenAI GPT
- `JobDescriptionParser` (line 718) - Analyzes job descriptions from URLs or text
- `TemplateDatabase` (line 823) - Manages interview question templates with ChromaDB vector storage
- `AsyncEnrollmentManager` (line 336) - Handles asynchronous speaker enrollment tasks

**Data Models:**
- `StructuredResume` (line 231) - Structured resume data
- `InterviewTemplate` (line 269) - Interview question templates with STAR/PREP frameworks
- `TemplateTier` (line 261) - Template lifecycle management (CORE/MEDIUM/SHORT/TEMPORARY)

### SQLite Compatibility
**CRITICAL:** pysqlite3 must be imported first (lines 6-11) to replace the system sqlite3 module for ChromaDB compatibility on some systems.

### Authentication & User Management
- `user_auth.py` - UserManager class, login_required decorator, session management
- `admin_auth.py` - Admin authentication with admin_required decorator
- `email_verification.py` - Email verification system
- Session-based auth with optional "remember me" functionality

### Payment System
- `payment_system.py` - Payment manager for premium features
- `payment_system_migration.py` - Database migration for payment tables
- Integration with user accounts for feature access control

### Voice & Mock Interviews
- `voice_interview_assistant.py` - Voice integration with Azure Speech Services
- `advanced_mock_interview_manager.py` - Advanced mock interview orchestration
- `advanced_mock_interview_session.py` - Individual mock interview sessions
- `eagle_speaker_recognition.py` - Picovoice Eagle speaker recognition (optional)
- `simple_speaker_detection.py` - Fallback speaker detection

### Resume Processing
- `enhanced_resume_parser.py` - Advanced resume parsing with entity extraction
- `resume_optimizer.py` - Resume optimization and improvement suggestions
- `resume_analysis_service.py` - Resume analysis service layer
- `version_comparator.py` - Compare different resume versions

### Task & Background Processing
- `task_manager.py` - Async task management with TaskStatus tracking
- Tasks run in background threads for long-running operations

### Referral & Analytics
- `referral_tracker.py` - Referral code tracking and rewards
- `referral_codes.py` - Referral code management
- `user_analytics.py` - User behavior analytics
- `device_fingerprint.py` - Device fingerprinting for fraud prevention

### Configuration
`config.py` contains dataclasses for all system configuration:
- `AudioConfig` - Audio processing settings
- `AzureConfig` - Azure Speech Services configuration
- `OpenAIConfig` - OpenAI API settings
- `TTSConfig` - Text-to-speech configuration
- `UserConfig` - User system policies (session timeout, password rules)

Global config instance available via `from config import config`

### Templates & UI
- `templates/` - Jinja2 HTML templates for all pages
- `static/` - Static assets (CSS, JS, images)
- Templates support bilingual interface (English/Chinese via `languages/`)

### Memory & Vector Search
- `memory_graph_manager.py` - Graph-based memory management
- `enhanced_memory_graph_manager.py` - Enhanced version with conflict resolution
- `openai_memory_manager.py` - OpenAI-powered memory management
- ChromaDB used for semantic search of interview templates

## Environment Variables

Required in `.env`:
```
OPENAI_API_KEY=your_openai_key
AZURE_SPEECH_KEY=your_azure_key
AZURE_SPEECH_REGION=eastus
PICOVOICE_ACCESS_KEY=your_picovoice_key  # Optional, for Eagle speaker recognition
```

## Key Integration Points

### Adding New API Endpoints
Flask routes are defined in `interview_assistant_system.py`. Use decorators:
- `@app.route()` - Public endpoints
- `@login_required` - Requires user authentication
- `@admin_required` - Requires admin privileges

### User Data Isolation
When querying databases, always filter by `user_id` from session to maintain data isolation between users. Use `get_current_user_id()` helper from `user_id_helper.py`.

### Template Generation Workflow
1. User uploads resume → `ResumeParser.parse_resume()`
2. User provides JD → `JobDescriptionParser.parse_job_description()`
3. System generates templates → `TemplateDatabase.generate_personalized_template()`
4. Templates stored with embeddings in ChromaDB for semantic search
5. Templates organized by tier for lifecycle management

### Mock Interview Flow
1. User selects templates → Creates session via `AdvancedMockInterviewManager`
2. Voice recording → Transcription via Azure Speech
3. Speaker diarization → Identifies interviewer vs interviewee
4. Real-time AI responses → Streaming via OpenAI API
5. Session analysis → Feedback generation

## Important Notes

- Port: Application runs on port 5001 by default
- CORS: Configured for `https://interviewasssistant.com`
- File uploads: Stored temporarily in `uploads/` directory
- Logging: Detailed logs in `data/logs/interview_system.log` (10MB rotation, 7-day retention)
- JSON parsing: Use `robust_json_parse()` function for handling malformed OpenAI responses
- Threading: Background tasks use daemon threads for enrollment and async operations

## Testing

Test files in repository:
- `test_eagle.py` - Eagle speaker recognition testing
- `test_speaker_recognition.py` - Speaker recognition testing
- `resume_analysis_test.py` - Resume analysis testing

## Migration Scripts

- `database_migration.py` - Database schema migrations
- `user_data_migration.py` - User data migrations
- `run_payment_migration.py` - Payment system migration runner
