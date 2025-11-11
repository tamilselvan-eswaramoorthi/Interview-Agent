import google.generativeai as genai
import logging
import threading


logger = logging.getLogger(__name__)


class GeminiHandler:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-flash-lite-latest")
        self.is_frozen = False
        
        self.on_response = None
        self.on_clear_transcription = None
        
    def set_frozen(self, frozen):
        self.is_frozen = frozen
        
    def process_transcript(self, transcript):
        def _process():
            if self.is_frozen:
                logger.info("AI responses are frozen. Skipping processing.")
                return
                
            if not self.model:
                logger.error("Gemini model is not available. Skipping API call.")
                return

            logger.info("Checking transcript with Gemini...")

            try:
                classification_prompt = f"""
                Is the following text a programming-related question, backend development question, or a technical interview question?
                This includes questions about APIs, databases, server architecture, microservices, DevOps, system design, or any programming concepts.
                Answer with only a single word: 'Yes' or 'No'.

                Text: "{transcript}"
                """
                classification_response = self.model.generate_content(classification_prompt)
                classification_result = classification_response.text.strip()

                logger.info(f"Classification: {classification_result}")

                if "Yes" in classification_result:
                    if self.on_clear_transcription:
                        self.on_clear_transcription()
                    
                    logger.info("Relevant question detected. Getting detailed answer...")
                    answer_prompt = f"""Please provide a clear and concise answer to the following question: {transcript}

For simple questions or definitions, provide a one-line answer.
For complex questions, provide a detailed explanation.

If your answer includes code examples, please provide them in Python programming language only. 
Format any code using triple backticks with 'python' as the language identifier like this:
```python
# your python code here
```

For backend development questions (APIs, databases, system design, etc.), provide practical answers.
Do not give unnecessary explanations - be direct and to the point."""
                    answer_response = self.model.generate_content(answer_prompt)

                    if self.on_response:
                        self.on_response(answer_response.text)
                else:
                    logger.info("Not a programming/backend/interview question. No further action taken.")

            except Exception as e:
                logger.error(f"Error with Gemini API: {e}")
                
        gemini_thread = threading.Thread(target=_process)
        gemini_thread.daemon = True
        gemini_thread.start()
