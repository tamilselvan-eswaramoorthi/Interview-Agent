import tkinter as tk
from tkinter import ttk, scrolledtext


class TranscriptionUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Interview Assistant")
        self.root.geometry("800x600")
        self.root.configure(bg='#f0f0f0')
        
        self.setup_ui()
        
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        title_label = ttk.Label(main_frame, text="AI Interview Assistant", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=(0, 10))
        
        self.start_button = ttk.Button(button_frame, text="Start Recording", 
                                      style='Success.TButton')
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(button_frame, text="Stop Recording", 
                                     state='disabled')
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_button = ttk.Button(button_frame, text="Clear")
        self.clear_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.freeze_button = ttk.Button(button_frame, text="Freeze AI")
        self.freeze_button.pack(side=tk.LEFT)
        
        self.status_label = ttk.Label(main_frame, text="Ready to start recording...", 
                                     foreground='green')
        self.status_label.grid(row=2, column=0, columnspan=2, pady=(0, 10))
        
        ttk.Label(main_frame, text="Live Transcription:", font=('Arial', 12, 'bold')).grid(
            row=3, column=0, sticky=tk.W, pady=(0, 5))
        
        self.transcription_text = scrolledtext.ScrolledText(
            main_frame, height=4, width=80, wrap=tk.WORD, font=('Arial', 10))
        self.transcription_text.grid(row=4, column=0, columnspan=2, pady=(0, 10), sticky=(tk.W, tk.E))
        
        ttk.Label(main_frame, text="AI Response:", font=('Arial', 12, 'bold')).grid(
            row=5, column=0, sticky=tk.W, pady=(0, 5))
        
        self.response_text = scrolledtext.ScrolledText(
            main_frame, height=18, width=80, wrap=tk.WORD, font=('Arial', 10))
        self.response_text.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        self._configure_text_tags()
        
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)
        main_frame.rowconfigure(6, weight=1)
        
    def _configure_text_tags(self):
        self.response_text.tag_configure("bold", font=('Arial', 10, 'bold'))
        self.response_text.tag_configure("italic", font=('Arial', 10, 'italic'))
        self.response_text.tag_configure("code", font=('Courier', 9), background='#f0f0f0')
        self.response_text.tag_configure("code_block", font=('Courier', 10), background='#e8e8e8', 
                                        relief='solid', borderwidth=1)
        self.response_text.tag_configure("code_header", font=('Arial', 11, 'bold'), 
                                        foreground='#0066cc')
        self.response_text.tag_configure("header", font=('Arial', 12, 'bold'))
        self.response_text.tag_configure("separator", foreground='#666666')
        
    def update_status(self, message, color='black'):
        self.root.after(0, lambda: self._update_status_ui(message, color))
        
    def _update_status_ui(self, message, color):
        self.status_label.config(text=message, foreground=color)
        
    def add_transcription(self, text):
        self.root.after(0, lambda: self._add_transcription_ui(text))
        
    def _add_transcription_ui(self, text):
        self.transcription_text.insert(tk.END, text + "\n")
        self.transcription_text.see(tk.END)
        
    def add_response(self, text):
        self.root.after(0, lambda: self._add_response_ui(text))
        
    def _add_response_ui(self, text):
        if text.startswith("GEMINI'S ANSWER:"):
            self.response_text.insert(tk.END, text + "\n", "header")
            self.response_text.insert(tk.END, "-"*50 + "\n", "separator")
        else:
            if '```' in text:
                self._handle_response_with_code_blocks(text)
            elif any(marker in text for marker in ['**', '*', '`', '#']):
                self._insert_markdown_text(text)
            else:
                self.response_text.insert(tk.END, text + "\n")
            self.response_text.insert(tk.END, "-"*50 + "\n", "separator")
        
        self.response_text.see(tk.END)
        
    def _handle_response_with_code_blocks(self, text):
        parts = text.split('```')
        
        explanation_parts = []
        code_blocks = []
        
        for i, part in enumerate(parts):
            if i % 2 == 0:
                if part.strip():
                    explanation_parts.append(part.strip())
            else:
                lines = part.split('\n')
                if lines and lines[0].strip() and not any(char in lines[0] for char in [' ', '\t', '(', ')', '{', '}', ';']):
                    language = lines[0].strip()
                    code_content = '\n'.join(lines[1:])
                else:
                    language = ""
                    code_content = part
                
                if code_content.strip():
                    code_blocks.append((language, code_content.strip()))
        
        if explanation_parts:
            explanation_text = '\n\n'.join(explanation_parts)
            self.response_text.insert(tk.END, "Explanation:\n", "code_header")
            if any(marker in explanation_text for marker in ['**', '*', '`', '#']):
                self._insert_markdown_text(explanation_text)
            else:
                self.response_text.insert(tk.END, explanation_text + "\n\n")
        
        for i, (language, code) in enumerate(code_blocks):
            if language:
                self.response_text.insert(tk.END, f"Code ({language}):\n", "code_header")
            else:
                self.response_text.insert(tk.END, "Code:\n", "code_header")
            
            self.response_text.insert(tk.END, code + "\n\n", "code_block")
    
    def _insert_markdown_text(self, text):
        lines = text.split('\n')
        for line in lines:
            self._process_markdown_line(line + '\n')
            
    def _process_markdown_line(self, line):
        i = 0
        while i < len(line):
            if line[i:i+2] == '**':
                end = line.find('**', i + 2)
                if end != -1:
                    bold_text = line[i+2:end]
                    self.response_text.insert(tk.END, bold_text, "bold")
                    i = end + 2
                    continue
            
            elif line[i] == '*' and line[i:i+2] != '**':
                end = line.find('*', i + 1)
                if end != -1:
                    italic_text = line[i+1:end]
                    self.response_text.insert(tk.END, italic_text, "italic")
                    i = end + 1
                    continue
            
            elif line[i] == '`':
                end = line.find('`', i + 1)
                if end != -1:
                    code_text = line[i+1:end]
                    self.response_text.insert(tk.END, code_text, "code")
                    i = end + 1
                    continue
            
            elif line[i] == '#' and (i == 0 or line[i-1] == '\n'):
                header_level = 0
                j = i
                while j < len(line) and line[j] == '#':
                    header_level += 1
                    j += 1
                
                if j < len(line) and line[j] == ' ':
                    header_text = line[j+1:]
                    self.response_text.insert(tk.END, header_text, "header")
                    break
            
            self.response_text.insert(tk.END, line[i])
            i += 1
        
    def clear_text(self):
        self.transcription_text.delete(1.0, tk.END)
        self.response_text.delete(1.0, tk.END)
        
    def clear_transcription(self):
        self.root.after(0, lambda: self.transcription_text.delete(1.0, tk.END))
