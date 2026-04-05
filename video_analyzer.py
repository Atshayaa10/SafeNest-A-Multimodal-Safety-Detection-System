import cv2
import glob
import time
import os
from moviepy import VideoFileClip
from colorama import Fore, Style, init
import whisper
from transformers import pipeline
from PIL import Image
from deepface import DeepFace
from chat_analyzer import ChatSafetyAnalyzer
from db_manager import db

init(autoreset=True)

class VideoSafetyAnalyzer:
    def __init__(self, text_analyzer=None, visual_alert_callback=None):
        print(f"{Fore.CYAN}[System] Initializing Video & Audio Vision Models...{Style.RESET_ALL}")
        
        # Prevent RAM Duplication: If Streamlit already has a ChatSafetyAnalyzer, use it!
        self.text_analyzer = text_analyzer if text_analyzer else ChatSafetyAnalyzer()
        self.visual_alert_callback = visual_alert_callback
        print(f"{Fore.GREEN}[System] Pipeline initialized. Models will dynamic-load to save RAM.{Style.RESET_ALL}")

    def extract_audio(self, video_path):
        import subprocess
        audio_path = "temp_extracted_audio.wav"
        print(f"{Fore.MAGENTA}[*] Extracting Audio stream from video (ffmpeg-cli)...{Style.RESET_ALL}")
        
        # Method 1: Robust FFmpeg Subprocess (bypass MoviePy frame-read issues)
        try:
            if os.path.exists(audio_path): os.remove(audio_path)
            
            # Extract audio to WAV using the absolute path to ffmpeg or shell path
            command = [
                'ffmpeg', '-y', '-i', video_path, 
                '-vn', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1', 
                audio_path
            ]
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return audio_path
        except Exception as e:
            print(f"{Fore.YELLOW}[Warning] FFmpeg CLI failed, trying fallback: {e}{Style.RESET_ALL}")
            
            # Method 2: Fallback to MoviePy
            try:
                with VideoFileClip(video_path) as video:
                    video.audio.write_audiofile(audio_path, logger=None)
                return audio_path
            except Exception as e2:
                print(f"{Fore.RED}[Error] Both extraction methods failed: {e2}{Style.RESET_ALL}")
                return None

    def analyze_audio_segment(self, audio_path, log_callback=None):
        import gc
        print(f"{Fore.MAGENTA}[*] Loading Whisper 'Base' Model into RAM...{Style.RESET_ALL}")
        whisper_model = whisper.load_model("base", device="cpu")
        print(f"{Fore.MAGENTA}[*] Transcribing Audio with safety-context steering...{Style.RESET_ALL}")
        
        # Use initial_prompt to fix cases like "brat" being transcribed as "bread"
        result = whisper_model.transcribe(audio_path, initial_prompt="brat, secret, parents, private, home, address, lonely, game")
        segments = result.get('segments', [])
        
        del whisper_model
        gc.collect()

        print(f"\n{Fore.GREEN}=== TRANSCRIPT SAFETY ANALYSIS ==={Style.RESET_ALL}")
        if not segments:
            print("No speech detected in audio.")
            
        for segment in segments:
            text = segment['text']
            start_time = time.strftime('%H:%M:%S', time.gmtime(segment['start']))
            
            is_safe, issues = self.text_analyzer.analyze_message(text)
            
            if log_callback:
                log_callback(f"[{start_time}] {text}", is_safe, issues)
            
            if not is_safe:
                print(f"{Fore.RED}[T={start_time}] AUDIO ALERT:{Style.RESET_ALL} '{text.strip()}'")
                for issue in issues:
                    print(f"    -> {issue}")

    def analyze_video_frames(self, video_path, frame_skip_rate=150, frame_callback=None):
        import gc
        print(f"\n{Fore.GREEN}=== VISUAL SAFETY ANALYSIS ==={Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}[*] Loading HuggingFace NSFW Vision Model into RAM...{Style.RESET_ALL}")
        nsfw_classifier = pipeline("image-classification", model="Falconsai/nsfw_image_detection", model_kwargs={"use_safetensors": False})
        
        # Grace period for OS to release file locks from MoviePy
        time.sleep(0.5)
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"{Fore.RED}[Error] Could not open video file: {video_path}{Style.RESET_ALL}")
            return

        frame_count = 0
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        if fps == 0: fps = 30
        
        try:
            while cap.isOpened():
                try:
                    ret, frame = cap.read()
                    if not ret:
                        # Sometimes OpenCV returns False momentarily, retry once
                        time.sleep(0.1)
                        ret, frame = cap.read()
                        if not ret: break
                except Exception as e:
                    print(f"{Fore.RED}[Error] Frame decode error at {frame_count}: {e}{Style.RESET_ALL}")
                    break
                
                if frame_count % fps == 0:  # Analyze 1 frame EVERY second
                    timestamp = time.strftime('%H:%M:%S', time.gmtime(frame_count / fps))
                    
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_img = Image.fromarray(rgb_frame)
                    
                    b64_img = None
                    def get_b64():
                        nonlocal b64_img
                        if b64_img is None:
                            import base64
                            _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
                            b64_img = base64.b64encode(buffer).decode('utf-8')
                        return b64_img
                    
                    # --- 1. NSFW Check ---
                    is_unsafe = False
                    nsfw_reason = ""
                    nsfwres = nsfw_classifier(pil_img)
                    top_label = nsfwres[0]['label'].lower()
                    top_score = nsfwres[0]['score']
                    
                    if top_label == 'nsfw' and top_score > 0.55:
                        is_unsafe = True
                        nsfw_reason = "NSFW Content Detected"
                        db.log_alert("NSFW_VIDEO", "Video frame visual scan", float(top_score), "Explicit/NSFW content detected visually", frame_image=get_b64())
                        
                        if self.visual_alert_callback:
                            self.visual_alert_callback("NSFW_VIDEO", "Visual Scan", float(top_score), "Explicit/NSFW content detected visually", get_b64())

                    # --- 2. Facial Sentiment/Distress Check ---
                    dominant_emotion = None
                    emotion_alert = False
                    try:
                        objs = DeepFace.analyze(img_path=rgb_frame, actions=['emotion'], enforce_detection=False, silent=True)
                        if objs:
                            dominant_emotion = objs[0]['dominant_emotion']
                            if dominant_emotion in ['fear', 'sad', 'angry', 'disgust']:
                                emotion_score = objs[0]['emotion'][dominant_emotion] / 100.0 if 'emotion' in objs[0] else 0.85
                                if self.visual_alert_callback:
                                    self.visual_alert_callback("EMOTION_DISTRESS", f"Facial Expression ({dominant_emotion})", float(emotion_score), f"Extreme emotion '{dominant_emotion}' tracking.", get_b64())
                                
                                is_unsafe = True
                                emotion_alert = True
                    except Exception:
                        pass
                    
                    if frame_callback:
                        # Draw visual alerts directly on the frame for the UI
                        ui_frame = cv2.resize(rgb_frame, (640, 360))
                        if is_unsafe:
                            # Draw a prominent red border or banner
                            cv2.rectangle(ui_frame, (0, 0), (640, 40), (255, 0, 0), -1)
                            alert_text = nsfw_reason if nsfw_reason else f"DISTRESS: {dominant_emotion.upper()}"
                            cv2.putText(ui_frame, f"!!! {alert_text} !!!", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                        elif dominant_emotion:
                            cv2.putText(ui_frame, f"Emotion: {dominant_emotion}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                        
                        frame_callback(ui_frame)
                    
                    if is_unsafe:
                        print(f"[T={timestamp}] {Fore.RED}Potential unsafe visual content{Style.RESET_ALL}")
                    else:
                        print(f"[T={timestamp}] {Fore.GREEN}Frame OK{Style.RESET_ALL}")
                    
                frame_count += 1
            
        except Exception as e:
            print(f"{Fore.RED}[Error] Visual analysis crashed: {e}{Style.RESET_ALL}")
        finally:
            cap.release()
            del nsfw_classifier
            gc.collect()

def run_pipeline():
    # Attempt to locate the first mp4 file natively uploaded to the directory
    mp4_files = glob.glob("*.mp4")
    if not mp4_files:
        print(f"{Fore.RED}No .mp4 video found in the current directory!{Style.RESET_ALL}")
        print("Please drag and drop your video file into the folder and run this script again.")
        return
        
    target_video = mp4_files[0]
    print(f"{Fore.CYAN}Target Video Found: {target_video}{Style.RESET_ALL}")
    
    analyzer = VideoSafetyAnalyzer()
    
    # Run Audio Extraction
    audio_file = analyzer.extract_audio(target_video)
    
    if audio_file:
        # 1. Analyze Spoken Transcript
        analyzer.analyze_audio_segment(audio_file)
        
        # Cleanup temp audio
        try:
            os.remove(audio_file)
        except:
            pass
            
    # 2. Analyze Visual Frames
    analyzer.analyze_video_frames(target_video)
    
    print(f"\n{Fore.GREEN}[System] Video Analysis Complete.{Style.RESET_ALL}")

if __name__ == "__main__":
    run_pipeline()
