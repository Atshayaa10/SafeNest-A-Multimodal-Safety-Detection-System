import re
import spacy
from transformers import pipeline
import warnings
from colorama import Fore, Style, init
import os
import json
from groq import Groq
from db_manager import db
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ignore hugging face warnings
warnings.filterwarnings("ignore")
# Initialize colorama
init(autoreset=True)

class ChatSafetyAnalyzer:
    def __init__(self):
        # We will lazy-load the heavy models ONLY when needed so the UI boots instantly!
        self.nlp = None
        self.toxicity_classifier = None

        # Initialize Groq LLM Agent for intention/grooming detection
        self.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        # PII Patterns
        self.phone_pattern = re.compile(r'\b(?:\+?1[-.●]?)?\(?([0-9]{3})\)?[-.●]?([0-9]{3})[-.●]?([0-9]{4})\b')
        self.email_pattern = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
    
    def _get_nlp(self):
        if self.nlp is None:
            print(f"{Fore.CYAN}[System] Lazy Loading SpaCy NER Model...{Style.RESET_ALL}")
            self.nlp = spacy.load("en_core_web_sm")
        return self.nlp
        
    def _get_toxicity(self):
        if self.toxicity_classifier is None:
            print(f"{Fore.CYAN}[System] Lazy Loading Toxicity Classifier...{Style.RESET_ALL}")
            # Use smaller, faster model (250MB vs 450MB) to fix MemoryErrors
            self.toxicity_classifier = pipeline("text-classification", model="martin-ha/toxic-comment-model", model_kwargs={"use_safetensors": False})
        return self.toxicity_classifier

    def analyze_message(self, message):
        flags = []
        issues = []
        
        # 1. PII Detection (Spacy & AI Verification)
        doc = self._get_nlp()(message)
        potential_locations = [ent.text for ent in doc.ents if ent.label_ in ['GPE', 'LOC', 'FAC']]

        # 2. UNIQUE FEATURE: LLM Agent for Grooming, Secrecy & Entity Verification
        try:
            # Gather local findings for AI context
            local_flags = []
            if self.phone_pattern.search(message): local_flags.append("PHONE_NUMBER")
            if self.email_pattern.search(message): local_flags.append("EMAIL_ADDRESS")
            
            # Pre-check Toxicity with BERT
            bert_result = self._get_toxicity()(message)[0]
            bert_toxic = bert_result['score'] > 0.6 and bert_result['label'].lower() == 'toxic'
            bert_score = bert_result['score']

            chat_completion = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a Child Safety Expert. Analyze the message for threat detection. \
                        Contextual findings from local scanners: {local_flags} and potential locations: {potential_locations}. \
                        Evaluate: 1. Grooming 2. Isolation 3. Belittling 4. Substances 5. Toxicity 6. PII Risk (Why sharing {local_flags} is dangerous here). \
                        Return ONLY JSON: {{\"is_grooming\": bool, \"is_location_confirmed\": bool, \"confirmed_location\": \"\", \"is_toxic\": bool, \"is_pii_dangerous\": bool, \"confidence_score\": float, \"reason\": \"str\"}}"
                    },
                    {
                        "role": "user",
                        "content": message
                    }
                ],
                model="llama-3.1-8b-instant",
                temperature=0,
                response_format={"type": "json_object"}
            )
            response = json.loads(chat_completion.choices[0].message.content)
            reason = response.get('reason', 'Threat detected by AI core.')

            # 1. PII Handling (Consolidated with AI reasoning)
            if local_flags or response.get('is_pii_dangerous') or response.get('is_location_confirmed'):
                flags.append("PII_ALERT")
                issues.append(f"PII SECURITY: {reason}")
                db.log_alert("PII_ALERT", message, 1.0, reason)

            # 2. Toxicity Arbitration
            if bert_toxic or response.get('is_toxic'):
                if response.get('is_toxic') or bert_score > 0.99:
                    flags.append("TOXICITY")
                    issues.append(f"INAPPROPRIATE: {reason}")
                    db.log_alert("TOXICITY", message, max(bert_score, 0.85), reason)
                else:
                    print(f"[System] Filtering BERT false positive: '{message}'")

            # 3. Grooming / Isolation
            if response.get('is_grooming'):
                flags.append("GROOMING_ALERT")
                issues.append(f"URGENT: {reason}")
                db.log_alert("GROOMING", message, response.get('confidence_score', 0.99), reason)

        except Exception as e:
            print(f"{Fore.RED}[DEBUG] API Error: {e}{Style.RESET_ALL}")
            # Minimal Fallback
            if self.phone_pattern.search(message):
                flags.append("PII_PHONE")
                issues.append("Phone number detected.")
            if self.email_pattern.search(message):
                flags.append("PII_EMAIL")
                issues.append("Email detected.")


        is_safe = len(flags) == 0
        return is_safe, issues


def chat_simulation():
    print(f"\n{Fore.GREEN}=== MelodyWings DB-Linked Chat Analyzer ==={Style.RESET_ALL}")
    print("Type a message to simulate a live chat stream. Type 'exit' to quit.")
    
    analyzer = ChatSafetyAnalyzer()
    
    print(f"\n{Fore.GREEN}[System Ready] Simulation Started.{Style.RESET_ALL}")
    print("-" * 50)
    
    while True:
        try:
            msg = input(f"{Fore.CYAN}User > {Style.RESET_ALL}")
            if msg.lower() == 'exit':
                print("Ending simulation.")
                break
            if not msg.strip():
                continue
                
            is_safe, issues = analyzer.analyze_message(msg)
            
            if is_safe:
                print(f"{Fore.GREEN}   [✓] Message Safe{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}   [!] ALERT TRIGGERED {Style.RESET_ALL}")
                for issue in issues:
                    print(f"       -> {issue}")
            
            print("-" * 50)
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    chat_simulation()
