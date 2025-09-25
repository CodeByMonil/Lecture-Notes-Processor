# Lecture Notes Processor – Multi‑Agent App (Gemini API)

> **IRWA Group Project – Y3S1 (Semester 2, 2025)**

## Group Members

| ID Number       | Name             |
|----------------|------------------|
| IT23178304      | ARIYARATHNA M.L  |
| IT23176942      | NAURUNNA L.A.D.P |
| IT23380950      | PERERA M.K.P.T.S |



## Project Overview

> An AI-powered app that transforms lecture content into clean transcripts, structured outlines, and professional slides.
> Built using Google Gemini API and Streamlit, it's perfect for summarizing and presenting lecture material efficiently.


## What it does
1. **Transcript Cleaner Agent** – accepts audio/video or raw text and produces a clean transcript (fewer filler words, better punctuation).  
2. **Key Points Extractor Agent** – extracts a hierarchical outline (topics → key points → bullets) with optional timestamps, using **structured JSON output**.  
3. **Slide Generator Agent** – turns the outline into a PowerPoint (`.pptx`).


# Quickstart & Setup

## Prerequisites
1. **Install Python 3.12** and **FFmpeg** (for audio processing).
2. **Create an API key (free)** in [Google AI Studio](https://console.cloud.google.com/), and copy it into the `.env` file.

## Setup & Run

1. **Clone the Repository**
   ```bash
   git clone <your-repo-url>
   cd IT3041-IRWA
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
