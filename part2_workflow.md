# MelodyWings: Part 2 Vision & Audio Pipeline

## Overview
Part 2 expands the safety net into **Multimodal Analysis**. While Chat (Part 1) monitors text, Part 2 listens to what is being said in audio and scans what is being shown in video streams to detect physical threats, emotional distress, and inappropriate visual content.

---

## 🛠️ The Tech Stack

### 1. The Audio Layer: `OpenAI Whisper` (Base Model)
**Purpose:** Converting spoken word into text for safety analysis.
*   **Whisper:** We use the `base` model to provide a balance between speed and accuracy. 
*   **Safety Steering:** We use an `initial_prompt` containing "safety keywords" (e.g., secrets, parents, private) to help the model correctly transcribe potential predatory context even in noisy environments.

### 2. The Visual Layer: `Hugging Face Transformers` (NSFW Vision)
**Purpose:** Identifying explicit or inappropriate visual content.
*   **Model (`Falconsai/nsfw_image_detection`):** This model classifies video frames into `Normal` or `NSFW`. 
*   **Safety Buffer:** We set a strict threshold of **0.55** to ensure that fast-paced or blurry scenes don't trigger false alarms while still catching explicit content.

### 3. The Emotional Intelligence Layer: `DeepFace`
**Purpose:** Monitoring for signs of fear, sadness, or extreme distress.
*   **DeepFace:** Uses deep convolutional neural networks to analyze facial expressions. 
*   **Distress Detection:** The system specifically tracks `Fear`, `Sadness`, and `Anger`. If these emotions dominate the child's face during a session, a `DISTRESS_ALERT` is logged to the database for human intervention.

---

## 🔄 The Execution Workflow

Whenever a video file is uploaded or a stream is processed:

1. **Audio Extraction**
   > `MoviePy` extracts the audio stream from the video.
2. **Speech-to-Text Pipeline**
   > `Whisper` transcribes the audio. The transcript is then passed back to the **Part 1 ChatSafetyAnalyzer** to check for Grooming, PII, or Toxicity.
3. **Frame-by-Frame Visual Scan**
   > `OpenCV` samples frames at regular intervals (1 frame per second).
4. **NSEW & Sentiment Check**
   > Each frame is simultaneously checked by the **NSFW Classifier** and **DeepFace**.
5. **Database Persistence**
   > Any positive detections (NSFW, High Distress, or Dangerous Speech) are instantly logged to the **PostgreSQL `safety_alerts` table** with timestamps and confidence scores.
6. **Moderator Dashboard Update**
   > The Human Moderator dashboard (Streamlit) refreshes to show the new alerts, including base64-encoded frame evidence from the video.
