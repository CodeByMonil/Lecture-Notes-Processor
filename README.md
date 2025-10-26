# Lecture Notes Processor – SlideCraft 🎓

> **IRWA Group Project – Y3S1 (July - December, 2025)**

## Group Members

| ID Number       | Name             |
|----------------|------------------|
| IT23178304      | ARIYARATHNA M.L  |
| IT23176942      | NAURUNNA L.A.D.P |
| IT23380950      | PERERA M.K.P.T.S |



## Project Overview
An AI-powered system that transforms lecture content into clean, readable text, enriched with reliable domain knowledge using Google Gemini 2.5 Flash embeddings. It generates a structured JSON outline from the content, which is then used to produce professional PowerPoint slides and an instructor guide PDF, streamlining lecture preparation and study material creation for educators and students.

---

## 🔹 What it Does
1. **Transcript Cleaner Agent** – accepts audio or text and produces a clean transcript (removes filler words, fixes punctuation).  
2. **Retriever Agent (KB)** – fetches relevant snippets from a pre-built **knowledge base** to improve accuracy (RAG).  
3. **Key Points Extractor Agent** – extracts a **hierarchical outline** (topics → sections → bullets) with optional timestamps, using structured JSON output.  
4. **Slide Generator Agent** – converts the outline into a polished **PowerPoint (`.pptx`)**.  
5. **Instructor Guide Agent** – generates a **lecture guideline PDF**, providing a structured delivery plan, engagement tips, and accessibility notes — especially helpful for **new lecturers** preparing their first sessions.

---

📌 **System Architecture Diagram:**  
![Agentic Flow](docs/sys_archi.png)  


## 🔹 Agentic Flow
The system follows an **agentic architecture**:

- **Transcript Cleaner** → cleans lecture input  
- **Retriever** → adds domain knowledge context  
- **Key Points Extractor** → builds outline (structured JSON)  
- **Slide Generator** → produces PowerPoint slides  
- **Instructor Guide** → generates structured lecture guideline PDF

---

# Quickstart & Setup

## Prerequisites
1. **Install Python 3.12** and **FFmpeg** (for audio processing).
2. **Create an API key (free)** in [Google AI Studio](https://aistudio.google.com/api-keys), and copy it into the `.env` file.

## Setup & Run

1. **Clone the Repository**
   ```bash
   git clone https://github.com/CodeByMonil/Lecture-Notes-Processor.git
   cd Lecture-Notes-Processor
   ```

2. **Create a Virtual Environment** (Python 3.12)
   ```bash
   py -3.12 -m venv .venv
   ```

3. **Activate the Virtual Environment**
   * On **Windows**:
     ```bash
     .venv\Scripts\activate
     ```
   * On **macOS/Linux**:
     ```bash
     source .venv/bin/activate
     ```

4. **Upgrade pip** and **Install Dependencies**
   ```bash
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

5. **Run the Streamlit App**
   ```bash
   streamlit run app.py
   ```

6. **Upload a Lecture** (audio: `.mp3` or `.wav`, text/PDF transcript) and click **Run**.  
   After processing, download the generated **`.pptx`** presentation from the UI.

---

## 🔹 Responsible AI Alignment
- **Transparency** → Users are informed that uploads are processed only within the app, stored temporarily on the backend, and never shared externally.  
- **Privacy Protection** → Files are auto-deleted after processing; only used for generating outputs.  
- **Ethical Handling** → No hidden data collection, no resale to third parties.  
- **Fairness** → Works equally for all lecture materials, with no bias toward specific subjects.  

---

## 🔹 Commercialization Pitch
This system can serve as an **AI assistant for educators and students**, streamlining lecture preparation and study material creation.

- **Target Users:**  
  - University **lecturers, professors, and instructors**  
  - **Students** needing structured notes or slides  

- **Value Proposition:**  
  - Saves time and effort in preparing lecture content  
  - Generates **professional-quality, consistent slides** automatically  
  - Allows users to focus on **teaching, learning, and engagement**  

- **Pricing Plans Comparison:**

| Feature                          | SlideCraft Free           | SlideCraft Pro (Premium)   |
|----------------------------------|--------------------------|---------------------------|
| Max Upload                       | 250MB                    | 1GB                       |
| Transcript-to-Outline Processing | ✅ Basic                 | ✅ Advanced               |
| Knowledge Base Enhancement        | ❌ Not Available         | ✅ Included               |
| Slide Templates & Formatting      | Standard                 | Advanced & Professional   |
| Upload Limit                      | Limited                  | Unlimited                 |
| Processing Priority               | Standard                 | Priority                  |
| Support                           | Community Support        | Premium Support           |
| Pricing                           | Free Forever             | 999 LKR / Month           |

    
---

## 🔹 Tech Stack
- **Frontend:** Streamlit  
- **Backend Agents:** Python (Transcript Cleaner, Retriever, Keypoint Extractor, Slide Generator)  
- **LLM:** Google **Gemini 2.5 Flash** (text, embeddings, multimodal transcription)  
- **Storage:** Local filesystem (replaceable with S3/Azure Blob for scale)  
- **Notebook:** `01_build_it_kb.ipynb` → builds Knowledge Base (KB) for domain-specific retrieval  

---
