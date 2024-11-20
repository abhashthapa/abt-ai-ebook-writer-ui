import os
import re
import requests
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from tkinter import ttk
import openai
from dotenv import load_dotenv
import time

# Load environment variables from .env file
load_dotenv()
tavily_api_url = "https://api.tavily.com/search"

# Initialize OpenAI client
def initialize_openai_client():
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        openai.api_key = openai_api_key
        return True
    else:
        messagebox.showerror("Error", "OpenAI API key not found in .env file.")
        return False

# Read the Tavily API key
def read_tavily_api_key():
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    if tavily_api_key:
        return tavily_api_key
    else:
        messagebox.showerror("Error", "Tavily API key not found in .env file.")
        return None

# Function to sanitize filenames
def sanitize_filename(filename):
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    # Remove non-ASCII characters
    filename = filename.encode('ascii', 'ignore').decode('ascii')
    # Truncate filename to a reasonable length
    return filename[:255]

# GUI Application Class
class EBookGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("E-Book Generator")
        if not initialize_openai_client():
            return
        self.tavily_api_key = read_tavily_api_key()
        if not self.tavily_api_key:
            return
        self.book_folder = ""
        self.toc = []
        self.chapters = []
        self.chapter_summaries = []
        self.total_cost = 0.0
        self.generate_images = tk.BooleanVar()
        self.generation_mode = "Fast generation"

        # Create the header frame
        self.header_frame = ttk.Frame(self.root)
        self.header_frame.pack(fill='x', padx=10, pady=5)

        # Add status label
        self.status_label = ttk.Label(self.header_frame, text="Status: Ready")
        self.status_label.pack(side=tk.LEFT, padx=5)

        # Add progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.header_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(side=tk.LEFT, fill='x', expand=True, padx=5)

        # Add timer label
        self.timer_label = ttk.Label(self.header_frame, text="Time: 00:00")
        self.timer_label.pack(side=tk.LEFT, padx=5)

        # Create the notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True)

        # Create frames for each tab
        self.generation_frame = ttk.Frame(self.notebook)
        self.toc_review_frame = ttk.Frame(self.notebook)
        self.final_content_frame = ttk.Frame(self.notebook)

        # Add tabs to the notebook
        self.notebook.add(self.generation_frame, text='E-Book Generation')
        self.notebook.add(self.toc_review_frame, text='TOC Review')
        self.notebook.add(self.final_content_frame, text='Final Content')

        # Initialize UI elements
        self.create_generation_tab()
        self.create_toc_review_tab()
        self.create_final_content_tab()

    def create_generation_tab(self):
        # Topic Frame
        topic_frame = ttk.Frame(self.generation_frame)
        topic_frame.pack(pady=10, padx=10, fill='x')
        ttk.Label(topic_frame, text="E-Book Topic (Min. 5 characters):").pack(side=tk.LEFT)
        self.topic_entry = ttk.Entry(topic_frame, width=50)
        self.topic_entry.pack(side=tk.LEFT)

        # Options Frame
        options_frame = ttk.Frame(self.generation_frame)
        options_frame.pack(pady=10, padx=10, fill='x')
        ttk.Checkbutton(
            options_frame,
            text="Generate images for chapters and cover page",
            variable=self.generate_images
        ).pack(anchor=tk.W)

        # Action Buttons Frame
        action_frame = ttk.Frame(self.generation_frame)
        action_frame.pack(pady=10, padx=10)
        ttk.Button(action_frame, text="Start Generation", command=self.start_generation).pack()

        # Features in the Pipeline Section
        pipeline_frame = ttk.Frame(self.generation_frame)
        pipeline_frame.pack(pady=10, padx=10, fill='x')

        ttk.Label(pipeline_frame, text="Features in the pipeline", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        features = [
            "- Proof reader in the Final Content tab",
            "- Exporting to PDF",
            "- More AI tools in the Final Content text editor like rewrite, summarize, expand and check grammar."
        ]
        for feature in features:
            ttk.Label(pipeline_frame, text=feature, foreground="gray").pack(anchor=tk.W, padx=10)

    def create_toc_review_tab(self):
        # TOC Label
        ttk.Label(self.toc_review_frame, text="Review and Edit the Table of Contents:").pack(anchor=tk.W, padx=10, pady=5)

        # TOC Text Area with monospace font and increased size
        toc_font_settings = ("Courier", 14)  # Monospace font with increased size
        self.toc_text_area = scrolledtext.ScrolledText(self.toc_review_frame, width=80, height=20, font=toc_font_settings)
        self.toc_text_area.pack(padx=10, pady=5)

        # Action Buttons Frame
        action_frame = ttk.Frame(self.toc_review_frame)
        action_frame.pack(pady=10)
        ttk.Button(action_frame, text="Continue", command=self.continue_after_toc_review).pack(side=tk.LEFT, padx=5)

    def create_final_content_tab(self):
        # Final Content Label
        ttk.Label(self.final_content_frame, text="Final E-Book Content:").pack(anchor=tk.W, padx=10, pady=5)

        # Toolbar Frame
        toolbar_frame = ttk.Frame(self.final_content_frame)
        toolbar_frame.pack(pady=5, padx=10, fill='x')

        # First row of buttons
        self.add_toolbar_button(toolbar_frame, "Bold", lambda: self.insert_md_syntax("**", "**"))
        self.add_toolbar_button(toolbar_frame, "Italic", lambda: self.insert_md_syntax("_", "_"))
        self.add_toolbar_button(toolbar_frame, "Underline", lambda: self.insert_md_syntax("<u>", "</u>"))
        self.add_toolbar_button(toolbar_frame, "Strikethrough", lambda: self.insert_md_syntax("~~", "~~"))
        for i in range(1, 6):
            self.add_toolbar_button(toolbar_frame, f"H{i}", lambda i=i: self.insert_md_syntax("#" * i + " ", ""))

        # Second row of buttons in a new frame
        second_row_frame = ttk.Frame(self.final_content_frame)
        second_row_frame.pack(pady=5, padx=10, fill='x')

        self.add_toolbar_button(second_row_frame, "Blockquote", lambda: self.insert_md_syntax("> ", ""))
        self.add_toolbar_button(second_row_frame, "Code Block", lambda: self.insert_md_syntax("```\n", "\n```"))
        self.add_toolbar_button(second_row_frame, "Inline Code", lambda: self.insert_md_syntax("`", "`"))
        self.add_toolbar_button(second_row_frame, "Horizontal Rule", lambda: self.insert_md_syntax("\n---\n", ""))
        self.add_toolbar_button(second_row_frame, "Link", lambda: self.insert_md_syntax("[text](url)", ""))
        self.add_toolbar_button(second_row_frame, "Image", lambda: self.insert_md_syntax("![alt text](image_url)", ""))
        self.add_toolbar_button(second_row_frame, "Numbered List", lambda: self.insert_md_syntax("1. ", ""))
        self.add_toolbar_button(second_row_frame, "Task List", lambda: self.insert_md_syntax("- [ ] ", ""))

        # Horizontal separator
        ttk.Separator(self.final_content_frame, orient='horizontal').pack(fill='x', padx=10, pady=5)

        # Content Text Area with increased font size
        font_settings = ("TkDefaultFont", 14)  # Increased by 4 points from the original
        self.content_text_area = scrolledtext.ScrolledText(self.final_content_frame, wrap=tk.WORD, font=font_settings)
        self.content_text_area.pack(fill='both', expand=True, padx=10, pady=5)

        # Action Buttons
        button_frame = ttk.Frame(self.final_content_frame)
        button_frame.pack(pady=5)
        ttk.Button(button_frame, text="Download as MD", command=self.download_as_md).pack(side=tk.LEFT, padx=5)

    def add_toolbar_button(self, parent, text, command):
        ttk.Button(parent, text=text, command=command).pack(side=tk.LEFT, padx=2)

    def insert_md_syntax(self, prefix, suffix):
        try:
            start = self.content_text_area.index(tk.SEL_FIRST)
            end = self.content_text_area.index(tk.SEL_LAST)
            selected_text = self.content_text_area.get(start, end)
            self.content_text_area.delete(start, end)
            self.content_text_area.insert(start, f"{prefix}{selected_text}{suffix}")
        except tk.TclError:
            # No text selected, insert at the current cursor position
            cursor_pos = self.content_text_area.index(tk.INSERT)
            self.content_text_area.insert(cursor_pos, f"{prefix}{suffix}")

    def start_generation(self):
        topic = self.topic_entry.get().strip()
        if len(topic) < 5:
            messagebox.showerror("Error", "Topic must be at least 5 characters long.")
            return

        self.book_folder = sanitize_filename(topic.replace(" ", "_"))
        if not os.path.exists(self.book_folder):
            os.makedirs(self.book_folder)

        # Clear TOC and content areas
        self.toc_text_area.delete('1.0', tk.END)
        self.content_text_area.delete('1.0', tk.END)

        # Start the timer
        self.start_timer()

        # Initialize agents
        self.initialize_agents()
        if not self.researcher:
            return

        # Update status
        self.update_status("Generating TOC", 0)

        # Research Information
        research_task = f"{topic}"
        research_data = self.researcher.execute_task(research_task)
        if not research_data:
            messagebox.showerror("Error", "Failed to fetch research data from Tavily API.")
            return

        # Generate and review TOC
        self.toc = self.generate_toc(topic, research_data)
        if not self.toc or all(not line.strip() for line in self.toc):
            messagebox.showerror("Error", "Failed to generate Table of Contents. Please try again or check your API keys.")
            return
        self.toc_text_area.insert(tk.END, "\n".join(self.toc))
        self.update_status("Ready", 0)  # Update status to Ready after TOC generation
        self.notebook.select(self.toc_review_frame)

    def initialize_agents(self):
        # Initialize agents
        self.researcher = ResearcherAgent(self.tavily_api_key)
        if not self.researcher:
            messagebox.showerror("Error", "Failed to initialize ResearcherAgent.")
            return
        self.content_organizer = ContentOrganizerAgent()
        self.writer = WriterAgent()
        self.designer = DesignerAgent()

    def generate_toc(self, topic, research_data):
        toc_response = self.content_organizer.execute_task({
            "query": topic,
            "answer": research_data.get("answer", ""),
            "results": research_data.get("results", [])
        })
        toc = toc_response.strip().split('\n')
        return toc

    def continue_after_toc_review(self):
        toc_content = self.toc_text_area.get("1.0", tk.END).strip()
        self.toc = toc_content.split('\n')
        self.notebook.select(self.final_content_frame)

        # Update status
        self.update_status("Generating Content", 15)  # TOC generation complete

        self.fast_generation()
        if self.generate_images.get():
            self.update_status("Generating Images", 75)
            self.designer.execute_task(self.book_folder, self.topic_entry.get().strip(), self.toc, self.chapters)
            messagebox.showinfo("Info", "Cover page and chapter images generated.")
        
        # Update status
        self.update_status("Finalizing Content", 90)

        final_md_content = self.merge_chapters_into_single_content(self.topic_entry.get().strip())
        self.content_text_area.insert(tk.END, final_md_content)
        self.notebook.select(self.final_content_frame)

        # Save the merged content as a markdown file
        self.save_as_markdown()

        # Update progress to 100%
        self.update_status("Complete", 100)

        # Stop the timer
        self.stop_timer()

    def fast_generation(self):
        num_chapters = len(self.toc)
        if self.generate_images.get():
            total_files = num_chapters * 2 + 2  # Chapters + Images + Merged + Cover
        else:
            total_files = num_chapters + 1  # Chapters + Merged

        progress_increment = 85 / total_files
        current_progress = 15  # Start from 15% after TOC generation

        for chapter_title in self.toc:
            if "SECTION" in chapter_title.upper():
                continue  # Skip sections
            safe_chapter_title = sanitize_filename(chapter_title)
            chapter_content, chapter_summary = self.generate_chapter(chapter_title)
            chapter_file = os.path.join(self.book_folder, f"{safe_chapter_title}.md")
            if not os.path.exists(os.path.dirname(chapter_file)):
                os.makedirs(os.path.dirname(chapter_file))
            with open(chapter_file, "w") as file:
                file.write(chapter_content)
            self.chapter_summaries.append(chapter_summary)
            self.chapters.append({"title": chapter_title, "content": chapter_content})
            self.root.update()

            # Update progress for each chapter
            current_progress += progress_increment
            self.update_status("Generating Content", current_progress)

            if self.generate_images.get():
                # Update progress for each image
                current_progress += progress_increment
                self.update_status("Generating Images", current_progress)

    def generate_chapter(self, chapter_title):
        # Replace [Book Name] and [Chapter Title] with actual book and chapter name during the generation
        task = f"Write a detailed content for {self.topic_entry.get().strip()} book with chapter called {chapter_title}. Use simple and understandable English. Follow the research data and do not create imaginary content. Use your creative freedom, it is suggested but not important to divide it into structured segments similar to an academic book, including any relevant examples, facts, quotes, and notable people or brands only if applicable. Conduct research on the web to gather accurate information and provide references for any key points made. Each chapter should be around 750 to 1000 words. Use your creative freedom, it is suggested but not important that each segments might include the following elements, all or a few or even none: Start with an engaging introduction that provides a brief overview of the segment. Include practical examples to illustrate key points. Incorporate factual information and quotes from credible sources or notable figures. Mention notable people or brands related to the subject matter. Add a short exercise or interactive activity at the end to engage readers and reinforce learning. Provide references for all the key points made to ensure accuracy and credibility. End with a conclusion with a summary that recaps the main points discussed in the chapter. Make sure that you go through past and future topics from the table of contents so that there are no redundant content in this chapter. Do not add prefatory statements, your own status, notes, apologizes and inconvenience, like you don't have access to internet, feel free to adjust, I cannot provide direct reference from web, fact checking or follow ups like sure, here is a detailed structure for your book. Do not keep unended sentences. Do not generate any elements if you don't have enough information. Make the content print ready without any remarks or feedback from your side. Output should be a well formatted mark down for example H1 for Chapter title, H2, H3 and other headings for other segment titles."
        chapter_content = self.writer.execute_task(task, {})
        chapter_content = chapter_content.replace("```markdown", "").replace("```", "")
        safe_chapter_title = sanitize_filename(chapter_title)
        chapter_image_path = f"{safe_chapter_title}_image.png"
        if self.generate_images.get():
            # Use a relative path for the chapter image
            chapter_image_markdown = f"![{chapter_title} Image]({chapter_image_path})\n\n"
            chapter_content = chapter_image_markdown + chapter_content
        summary_task = f"Summarize the following chapter content in 2-3 sentences:\n\n{chapter_content}"
        chapter_summary = self.writer.execute_task(summary_task, {})
        return chapter_content, chapter_summary

    def merge_chapters_into_single_content(self, topic):
        final_md_content = f"# {topic}\n\n"
        final_md_content += "![Cover Page](cover_page.png)\n\n"
        final_md_content += "### Author: OpenAI's GPT-4o\n"
        final_md_content += "### Designer: DALL·E 3\n\n"
        final_md_content += "## Table of Contents\n\n"
        for chapter in self.chapters:
            final_md_content += f"- {chapter['title']}\n"
        final_md_content += "\n"
        for chapter in self.chapters:
            # Assume the chapter content already includes the chapter title and image
            final_md_content += f"\n\n{chapter['content']}\n\n"
        final_md_content += "Thank you for reading.\n"
        return final_md_content

    def save_as_markdown(self):
        # Use the sanitized book name for the markdown file
        book_name = sanitize_filename(self.topic_entry.get().strip())
        file_path = os.path.join(self.book_folder, f"{book_name}.md")
        content = self.content_text_area.get("1.0", tk.END)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            messagebox.showinfo("Success", f"File saved successfully at {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {e}")

    def download_as_md(self):
        # Use the sanitized book name for the markdown file
        book_name = sanitize_filename(self.topic_entry.get().strip())
        file_path = os.path.join(self.book_folder, f"{book_name}.md")
        
        # Check if file already exists and append a number if necessary
        base_file_path = file_path
        counter = 1
        while os.path.exists(file_path):
            file_path = os.path.join(self.book_folder, f"{book_name}_{counter:02}.md")
            counter += 1

        content = self.content_text_area.get("1.0", tk.END)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            messagebox.showinfo("Success", f"File downloaded successfully as {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to download file: {e}")

    def update_status(self, message, progress):
        self.status_label.config(text=f"Status: {message}")
        self.progress_var.set(progress)
        self.root.update_idletasks()

    def start_timer(self):
        self.start_time = time.time()
        self.timer_running = True
        self.update_timer()

    def update_timer(self):
        if self.timer_running:
            elapsed_time = int(time.time() - self.start_time)
            minutes, seconds = divmod(elapsed_time, 60)
            self.timer_label.config(text=f"Time: {minutes:02}:{seconds:02}")
            self.root.after(1000, self.update_timer)

    def stop_timer(self):
        self.timer_running = False

# Custom Agent Classes

class ResearcherAgent:
    def __init__(self, tavily_api_key):
        self.tavily_api_key = tavily_api_key
        self.name = "Researcher"
        self.role = "Gather information"
        self.goal = "Collect and synthesize comprehensive and reliable data relevant to the ebook's topic"
        self.backstory = "Expert in data gathering and internet research, with a keen eye for detail"
        self.verbose = True
        self.llm = "gpt-4o"
        self.allow_delegation = True
        self.tools = ["advanced_llm", "web_access", "tavily_api"]

    def execute_task(self, task):
        print(f"\n{self.name} is executing the task: {task}\n")
        try:
            tavily_response = requests.post(
                tavily_api_url,
                headers={"Content-Type": "application/json"},
                json={"query": task, "api_key": self.tavily_api_key}
            )
            if tavily_response.status_code == 200:
                tavily_data = tavily_response.json()
                research_data = self.validate_data(tavily_data)
                if not research_data.get("answer"):
                    research_data['answer'] = self.generate_answer_from_results(research_data.get("results", []), task)
                print(research_data)
                return research_data
            else:
                print(f"Error fetching data from Tavily API: {tavily_response.status_code} - {tavily_response.text}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Exception during Tavily API call: {e}")
            return None

    def validate_data(self, tavily_data):
        validated_data = {
            "answer": tavily_data.get("answer", ""),
            "query": tavily_data.get("query", ""),
            "images": tavily_data.get("images", []),
            "results": tavily_data.get("results", []),
            "response_time": tavily_data.get("response_time", ""),
            "follow_up_questions": tavily_data.get("follow_up_questions", [])
        }
        return validated_data

    def generate_answer_from_results(self, results, query):
        if not results:
            return ""
        search_snippets = "\n".join([result.get('snippet', '') for result in results if result.get('snippet')])
        messages = [
            {"role": "system", "content": "You are an assistant that summarizes search results into a coherent answer."},
            {"role": "user", "content": f"Based on the following search results, provide a comprehensive answer to the query '{query}':\n\n{search_snippets}"},
        ]
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=500,
            temperature=0.7,
        )
        answer = response['choices'][0]['message']['content'].strip()
        return answer

class ContentOrganizerAgent:
    def __init__(self):
        pass

    def execute_task(self, data):
        if not data['answer'] and not data['results']:
            return "Unable to generate Table of Contents due to lack of research data."
        messages = [
            {"role": "system", "content": "You are an assistant that helps generate a table of contents for an e-book."},
            {"role": "user", "content": f"Based on the following research data, generate a detailed table of contents for an e-book on '{data['query']}':\n\n{data['answer']}\n\nTable of contents should only have chapters, but no sub chapters or sections. Table of content should be systematic, should have high level topics and gradually increase the depth on the topic rather than a random list. Chapters should have CHAPTER 01 - Chapter name, CHAPTER 02 - Chapter name and so on as prefix. Do not include the text Table of contents as a chapter. Do not generate prefatory or introductory statements. Just show the output."},
        ]
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=500,
            temperature=0.7,
        )
        toc = response['choices'][0]['message']['content'].strip()
        return toc

class WriterAgent:
    def __init__(self):
        pass

    def execute_task(self, task, research_data):
        messages = [
            {"role": "system", "content": "You are an assistant that writes content for e-books."},
            {"role": "user", "content": f"{task}\n\nResearch Data:\n{research_data}"},
        ]
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=1500,
            temperature=0.7,
        )
        content = response['choices'][0]['message']['content'].strip()
        return content

class DesignerAgent:
    def __init__(self):
        self.name = "Designer"
        self.role = "Generate cover page design"
        self.goal = "Create a relevant, minimal, and beautiful cover page using DALL-E 3"
        self.backstory = "Creative designer with a knack for generating stunning visuals"
        self.verbose = True
        self.llm = "dalle-3"
        self.allow_delegation = True
        self.tools = ["advanced_llm", "image_generation"]

    def generate_cover_prompt(self, book_title):
        return f"Create an artwork design on subject '{book_title}'. The design should be minimal, beautiful, and relevant to the topic. The artwork should not be too imaginary. The artwork should not have actual book, book cover, book mockups and texts."

    def generate_chapter_prompt(self, chapter_title, chapter_summary):
        # Base prompt text
        base_prompt = f"Create an artwork design for the chapter titled '{chapter_title}'. The design should be minimal, beautiful, and relevant to the topic. The artwork should not be too imaginary. The artwork should not have actual book, book cover, book mockups and texts. Here is a brief summary of the chapter: "
        
        # Calculate the maximum allowed length for the summary
        max_summary_length = 3800 - len(base_prompt)
        
        # Truncate the summary if necessary
        if len(chapter_summary) > max_summary_length:
            chapter_summary = chapter_summary[:max_summary_length] + "..."
        
        return base_prompt + chapter_summary

    def execute_task(self, book_folder, topic, toc, chapters):
        # Generate cover page design
        cover_prompt = self.generate_cover_prompt(topic)
        print(f"Prompt for DALL-E 3: {cover_prompt}")

        # Use DALL-E 3 to generate the cover page design
        completion_response = openai.Image.create(
            model="dall-e-3",
            prompt=cover_prompt,
            n=1,
            size="1024x1024",
            quality="hd",
            style="vivid"
        )

        # Save the generated image
        image_url = completion_response['data'][0]['url']
        image_response = requests.get(image_url)
        if image_response.status_code == 200:
            cover_image_path = os.path.join(book_folder, "cover_page.png")
            with open(cover_image_path, "wb") as file:
                file.write(image_response.content)
            print(f"Cover page design saved as {cover_image_path}")
        else:
            print("Failed to download the cover page design.")

        # Generate prompts and images for each chapter
        for chapter in chapters:
            chapter_title = chapter['title']
            chapter_prompt = self.generate_chapter_prompt(chapter_title, chapter['content'])
            print(f"Prompt for DALL-E 3: {chapter_prompt}")

            # Use DALL-E 3 to generate the chapter image
            completion_response = openai.Image.create(
                model="dall-e-3",
                prompt=chapter_prompt,
                n=1,
                size="1024x1024",
                quality="hd",
                style="vivid"
            )

            # Save the generated image
            image_url = completion_response['data'][0]['url']
            image_response = requests.get(image_url)
            if image_response.status_code == 200:
                safe_chapter_title = sanitize_filename(chapter_title)
                image_path = os.path.join(book_folder, f"{safe_chapter_title}_image.png")
                with open(image_path, "wb") as file:
                    file.write(image_response.content)
                print(f"Chapter image saved as {image_path}")
            else:
                print(f"Failed to download the image for chapter: {chapter_title}")

if __name__ == "__main__":
    root = tk.Tk()
    app = EBookGeneratorApp(root)
    root.mainloop()
