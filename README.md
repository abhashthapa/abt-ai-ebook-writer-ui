# ABT E-Book Writer UI

This project is a GUI Python application for creating e-books using AI agents. It generates table of content, content, designs cover pages for the book and each chapters, and exports into separate and merged MD and PDF files.

**Being a non-programmer, I used [Cursor](https://www.cursor.com/) and gpt-4o to produce this script.**


## Features

- Generate e-books with table of contents, chapters and images using AI(OpenAI).
- Review and edit the Table of Contents.
- Edit the final content through simple Markdown editor.
- Save the final content as a Markdown file. Exporting PDF is not supported yet.

https://github.com/user-attachments/assets/1c3f5b11-ee40-4a6f-a4b0-7eeb0ac4c061

<sup>50x speed, total generation duration: ~9mins</sup>

📖 Sample ebook generated

[Color Voyages Exploring the Psychology of Palettes.pdf](https://github.com/user-attachments/files/17831833/Color.Voyages.Exploring.the.Psychology.of.Palettes.pdf)


---
 
## Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/abhashthapa/abt-ai-ebook-writer-ui.git
   cd abt-ai-ebook-writer-ui
   ```

2. **Create a virtual environment and activate it**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install the dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Create a `.env` file**:
   - Copy the `.env.example` file to `.env` and fill in your API keys.

## Running the Application

Run the following command to start the application:


## Usage
```bash
python ebook_project_ui.py
```


## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.
