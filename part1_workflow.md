# MelodyWings: Part 1 Architecture & Workflow

## Overview
Part 1 of the MelodyWings safety system focuses on **Real-Time Text and Chat Moderation**. The goal is to analyze an ongoing stream of chat messages and instantly identify three major threats: Personally Identifiable Information (PII) leakage, Toxic Behavior (Cyberbullying), and Predatory Grooming.

To achieve enterprise-grade accuracy, we implemented a layered pipeline where the message passes through hard-coded rules, simple AI classifiers, and finally, a deep cognitive LLM.

---

## 🛠️ The Tech Stack

### 1. The Filtering Layer: Python `re` (Regex) & `spaCy`
**Purpose:** Lightning-fast extraction of concrete Personal Information.
*   **Regex:** Checks for strict alphanumeric patterns like Phone Numbers and Emails.
*   **spaCy (`en_core_web_sm`):** Uses Named Entity Recognition (NER) to understand sentence structure and pull out Geopolitical Entities (Cities, States, Countries) or specific facilities that a child might accidentally share.

### 2. The Classification Layer: Hugging Face `Transformers`
**Purpose:** Detecting cyberbullying or abuse.
*   **Model (`unitary/toxic-bert`):** Instead of relying on a simple list of "bad words", this Hugging Face NLP model analyzes the context of the sentence. It assigns a confidence score to determine if the message is highly toxic, offensive, or threatening.

### 3. The Cognitive Agent Layer: Groq API (`Llama-3.1-8b-instant`) **[Unique Feature]**
**Purpose:** Detecting subtle, manipulative behavior and predatory grooming.
*   **Why we upgraded to Llama-3:** A predator rarely uses swear words when manipulating a child. They use subtle phrases like *"Let's move to Snapchat"* or *"Don't tell your parents"*. Traditional models miss this. 
*   **How it works:** We integrated the Groq API to run Meta's open-source Llama-3 model. It acts as an autonomous Child Safety Agent, receiving the message and outputting a strict JSON determination on whether the intent is dangerous flirting, isolation, or grooming. Because Groq uses specialized LPU architecture, this massive AI model returns answers in milliseconds, making it viable for live chat.

---

## 🔄 The Execution Workflow

Whenever a user hits "Enter" in the chat, the following pipeline executes asynchronously:

1. **Message Ingestion**
   > The raw string message is captured.
2. **PII Firewall Check**
    > The message is scanned by Regex and `spaCy`.
    > *If an address or phone number is found -> Trigger `PII_ALERT`*
3. **Sentiment & Toxicity Check**
    > The message is sent to the local Hugging Face `ToxicBERT` model.
    > *If the toxic confidence score exceeds 80% -> Trigger `TOXICITY` Alert*
4. **Behavioral Agent Validation**
    > The message is routed to the Llama-3 agent via Groq. The model is specifically prompted to strictly look for isolation requests.
    > *If flagged by the LLM -> Trigger `GROOMING_ALERT` along with the AI's exact reasoning.*
5. **Output Delivery**
    > The system aggregates all the alerts. If any flag was triggered, it immediately isolates the message and alerts the Human Moderator dashboard. If the array is empty, it clears the message as `Safe`.
