# 🛡️ SafeNest: A Multimodal Safety Detection System

**SafeNest** is a nonprofit prototype platform designed to support neurodivergent children and children with special needs. By connecting them with volunteer mentors for personalized, interest-based learning, SafeNest ensures a secure environment through a multi-layered AI defense system that detects safety concerns in real time.

---

## 🚀 Key Features

### 1. Live Chat Analysis
- **Intention & Grooming Detection**: Powered by **Llama-3 (via Groq)** to identify isolation attempts and predatory patterns.
- **Toxicity Filtering**: Real-time analysis of profanity or inappropriate language using **ToxicBERT**.
- **PII Leak Prevention**: Automatic detection of personal information (address, phone number, email) using **SpaCy** and Regex.

### 2. Multi-modal Video & Audio Scanning
- **Visual Threat Detection**: Frame-by-frame analysis for explicit or unsafe visual content.
- **Audio Safety Pipeline**: Transcription and safety processing of video audio via **OpenAI Whisper**.
- **Visual Evidence Logging**: Flagged frames are automatically captured and stored for human review.

### 3. Safety Command Center
- **Real-Time Alerts**: Instant visual notifications on the Streamlit dashboard when a threat is detected.
- **Comprehensive Auditing**: Export safety data to **CSV and PDF reports** for investigations and audits.

---

## 🛠️ Technology Stack

- **Frontend**: [Streamlit](https://streamlit.io/)
- **Core Reasoning**: [Llama-3-8b (Groq)](https://groq.com/)
- **Text Safety**: [ToxicBERT](https://huggingface.co/martin-ha/toxic-comment-model)
- **Natural Language**: [SpaCy](https://spacy.io/)
- **Audio Engine**: [OpenAI Whisper](https://github.com/openai/whisper)
- **Vision Engine**: [DeepFace](https://github.com/serengil/deepface) / OpenCV

---

## ⚙️ Installation & Setup

### Prerequisites
- Python 3.9+
- [Groq API Key](https://console.groq.com/)

### Quick Start
1. **Clone and Enter**:
   ```bash
   git clone https://github.com/Atshayaa10/melody_wings.git
   cd melody_wings
   ```
2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```
3. **Configure Environment**:
   Add your API key to a `.env` file:
   ```env
   GROQ_API_KEY=your_key_here
   ```
4. **Launch Dashboard**:
   ```bash
   streamlit run app.py
   ```

---

## ⚖️ Safety Philosophy
SafeNest operates on a **Multimodal Arbitration** principle. By combining text, audio, and visual intelligence, the system provides a holistic safety net that adapts to the unique communication needs of neurodivergent children, ensuring every interaction is supportive and secure.
