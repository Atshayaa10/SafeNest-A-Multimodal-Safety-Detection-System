from chat_analyzer import ChatSafetyAnalyzer
from colorama import Fore, Style

def test_accuracy():
    analyzer = ChatSafetyAnalyzer()
    
    test_cases = [
        ("I live in New York", True, "Location should be detected"),
        ("My name is Vincent", False, "Vincent should NOT be detected as a location"),
        ("You are such a brat", True, "Brat should be detected as belittling/grooming"),
        ("Sprite.", False, "Sprite should be SAFE (Suppressed False Positive)"),
        ("I don't remember asking you a goddamn thing.", True, "Profanity should be detected as ALERT")
    ]
    
    print(f"\n{Fore.CYAN}=== Final Accuracy Verification ==={Style.RESET_ALL}")
    
    # Pre-load models (lazy loading check)
    analyzer.analyze_message("Initialize everything")
    
    for msg, expected_flag, desc in test_cases:
        print(f"\nTesting: '{msg}'")
        is_safe, issues = analyzer.analyze_message(msg)
        print(f"Result: {'SAFE' if is_safe else 'ALERT'}")
        for issue in issues:
            print(f"  - {issue}")
        
        # Check against expectation
        has_alert = not is_safe
        if has_alert != expected_flag:
            print(f"{Fore.RED}FAILURE: {desc} (Expected {expected_flag}, got {has_alert}){Style.RESET_ALL}")
        else:
            print(f"{Fore.GREEN}SUCCESS: {desc}{Style.RESET_ALL}")

if __name__ == "__main__":
    test_accuracy()
