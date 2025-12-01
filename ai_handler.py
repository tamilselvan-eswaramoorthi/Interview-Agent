import google.generativeai as genai
import logging
import threading
from PIL import Image


logger = logging.getLogger(__name__)


class GeminiHandler:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-flash-lite-latest")
        self.vision_model = genai.GenerativeModel("gemini-2.5-pro")
        self.is_frozen = False
        
        self.on_response = None
        self.on_clear_transcription = None
        self.on_image_response = None
        
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
    
    def process_image(self, image_path):
        """Process an image containing MCQ or coding question"""
        def _process_image():
            if self.is_frozen:
                logger.info("AI responses are frozen. Skipping image processing.")
                return
            
            if not self.vision_model:
                logger.error("Gemini vision model is not available. Skipping image processing.")
                return
            
            logger.info(f"Processing image with Gemini: {image_path}")
            
            try:
                # Load the image
                image = Image.open(image_path)
                
                # Create a concise prompt for MCQ and coding questions
                prompt = """Analyze this image. It contains either a Multiple Choice Question (MCQ) or a Coding Question.

**CRITICAL INSTRUCTIONS - Follow exactly:**

1. **If it's an MCQ:**
   - Respond with ONLY the correct option letter (A, B, C, or D)
   - Nothing else. No explanation. No question restatement.
   - Example response: "C"

2. **If it's a Coding Question:**
   - Respond with ONLY the Python code solution
   - No problem restatement
   - No explanations or approach description
   - No complexity analysis
   - No markdown code blocks
   - No comments in the code
   - Just pure, executable Python code

Your response:"""

                # Generate response with image
                response = self.vision_model.generate_content([prompt, image])
                
                logger.info("Image analysis complete")
                
                # Send response through callback
                if self.on_image_response:
                    self.on_image_response(response.text, image_path)
                elif self.on_response:
                    # Fallback to regular response handler
                    header = f"📸 IMAGE ANALYSIS: {image_path.split('/')[-1]}\n"
                    self.on_response(header + response.text)
                
            except Exception as e:
                logger.error(f"Error processing image with Gemini: {e}")
                if self.on_response:
                    self.on_response(f"Error processing image: {str(e)}")
        
        image_thread = threading.Thread(target=_process_image)
        image_thread.daemon = True
        image_thread.start()
