# Plan: Sanitize Repository and Secure API Keys

The repository push was rejected by GitHub because a Groq API Key was detected in the git history. This plan outlines the steps to remove the secret from the history and secure it using environment variables.

## User Review Required

> [!IMPORTANT]
> **API Key Rotation**: The Groq API key has been "exposed" in the local git history and attempted to be pushed. Even though the push failed, it is **highly recommended** to rotate (revoke and generate a new) API key in the Groq dashboard after this process is complete.

> [!WARNING]
> **Git History Reset**: This plan involves rewriting the local git history to remove the secret. Since the previous push failed, this is safe to do and will not affect other collaborators (unless you have successfully pushed these commits to another remote).

## Proposed Changes

### Configuration and Security

#### [MODIFY] [.gitignore](file:///c:/Users/atsha/Downloads/melodywings/.gitignore)
- Add `.env` to prevent environment variables from being committed.
- Add other common Python exclusions (e.g., `__pycache__`, `.venv`).

#### [NEW] [.env](file:///c:/Users/atsha/Downloads/melodywings/.env)
- Create a new environment file to store `GROQ_API_KEY`.

---

### Core Application

#### [MODIFY] [chat_analyzer.py](file:///c:/Users/atsha/Downloads/melodywings/chat_analyzer.py)
- Import `dotenv` and load environment variables.
- Replace the hardcoded API key with `os.getenv("GROQ_API_KEY")`.

---

### Git History Sanitization

#### [COMMAND] Git History Reset
1. Check the number of local commits.
2. Perform a `git reset --soft` to the beginning.
3. Re-add files (ensuring `.env` is ignored).
4. Create a fresh initial commit.
5. Push to GitHub.

## Open Questions

- Do you have any other secrets hardcoded in other files (e.g., `app.py` or `video_analyzer.py`)? I will perform a quick grep search to check.

## Verification Plan

### Automated Tests
- Run `python chat_analyzer.py` to ensure it still connects correctly using the `.env` key.
- Verify with `git log -p` that the secret is no longer visible in any commit history.

### Manual Verification
- Attempt the `git push` again after the history has been cleaned.
