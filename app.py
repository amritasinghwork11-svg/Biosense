"""
BioSense — AI Biodiversity Monitor
Powered by Gemma 4 (via Ollama) | Hackathon Demo
"""

import sys
import io
import os
os.environ["PYTHONIOENCODING"] = "utf-8"

import gradio as gr
import ollama
import base64
import csv
from datetime import datetime
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────────
MODEL = "gemma3:4b"           # swap to gemma3:12b or gemma3:27b for better accuracy
LOG_FILE = "sightings_log.csv"
IUCN_CATEGORIES = {
    "EX": "Extinct",
    "EW": "Extinct in the Wild",
    "CR": "Critically Endangered 🔴",
    "EN": "Endangered 🟠",
    "VU": "Vulnerable 🟡",
    "NT": "Near Threatened",
    "LC": "Least Concern 🟢",
    "DD": "Data Deficient",
    "NE": "Not Evaluated",
}

# ── Prompt ───────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are BioSense, an expert field biologist and wildlife identification AI assistant.
You help forest rangers, researchers, and conservationists identify species from photos and field observations.

When given an image or description, always respond in this exact JSON format:
{
  "common_name": "...",
  "scientific_name": "...",
  "category": "Animal/Plant/Bird/Insect/Track/Unknown",
  "iucn_status": "LC/NT/VU/EN/CR/EW/EX/DD/NE",
  "habitat": "...",
  "found_in_india": true/false,
  "ranger_action": "...",
  "interesting_fact": "...",
  "confidence": "High/Medium/Low",
  "warning": "..."
}

For ranger_action, give a specific, practical instruction (e.g., 'Maintain 50m distance, log sighting, alert DFO if mother with cubs').
For warning, mention any danger or legal protection relevant to rangers.
Always prioritize species found in Indian forests (Rajasthan, Central India, Western Ghats).
If you cannot identify the species, still return the JSON with your best guess and Low confidence."""

# ── CSV Logger ───────────────────────────────────────────────────────────────
def init_log():
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp", "common_name", "scientific_name",
                "iucn_status", "category", "confidence", "location_note"
            ])

def log_sighting(data: dict, location_note: str = ""):
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            data.get("common_name", "Unknown"),
            data.get("scientific_name", ""),
            data.get("iucn_status", ""),
            data.get("category", ""),
            data.get("confidence", ""),
            location_note,
        ])

# ── Gemma 4 Call ─────────────────────────────────────────────────────────────
def identify_species(image_path, description, location_note, language):
    """Send image + description to Gemma 4 and parse response."""
    import json, re

    lang_instruction = {
        "English": "Write all JSON values in English.",
        "Hindi": "IMPORTANT: You MUST write the values for ranger_action, warning, habitat, and interesting_fact fields in Hindi (Devanagari script). Keep JSON keys in English. Example: \"ranger_action\": \"100 मीटर की दूरी बनाए रखें और DFO को तुरंत सूचित करें।\"",
        "Rajasthani": "IMPORTANT: You MUST write the values for ranger_action, warning, habitat, and interesting_fact fields in Hindi/Rajasthani (Devanagari script). Keep JSON keys in English.",
    }.get(language, "Write all JSON values in English.")

    user_prompt = f"{lang_instruction}\n\nField observation: {description or 'Please identify the species in this image.'}"

    try:
        if image_path:
            # Encode image to base64
            with open(image_path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode()

            response = ollama.chat(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": user_prompt,
                        "images": [img_b64],
                    },
                ],
            )
        else:
            response = ollama.chat(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
            )

        raw = response["message"]["content"]

        # Extract JSON from response
        json_match = re.search(r"\{.*\}", raw, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
        else:
            data = {"common_name": "Unable to parse", "confidence": "Low", "ranger_action": raw}

        return data, raw

    except Exception as e:
        return {"common_name": "Error", "ranger_action": str(e), "confidence": "Low"}, str(e)


# ── Format Output ─────────────────────────────────────────────────────────────
def format_output(data: dict) -> str:
    iucn = data.get("iucn_status", "NE")
    iucn_label = IUCN_CATEGORIES.get(iucn, iucn)
    confidence = data.get("confidence", "Low")
    conf_emoji = {"High": "🟢", "Medium": "🟡", "Low": "🔴"}.get(confidence, "❓")

    found_india = "✅ Found in India" if data.get("found_in_india") else "⚠️ Not typically found in India"

    output = f"""
## 🌿 BioSense Identification Report

### {data.get('common_name', 'Unknown Species')}
**Scientific Name:** *{data.get('scientific_name', 'N/A')}*
**Category:** {data.get('category', 'Unknown')}
**Confidence:** {conf_emoji} {confidence}
{found_india}

---

### 🔴 Conservation Status
**IUCN Category:** {iucn} — {iucn_label}

---

### 🌍 Habitat
{data.get('habitat', 'N/A')}

---

### 🎯 Ranger Action
> {data.get('ranger_action', 'N/A')}

---

### ⚠️ Warning / Legal Note
{data.get('warning', 'No specific warning.')}

---

### 💡 Interesting Fact
{data.get('interesting_fact', 'N/A')}

---
*Sighting logged at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""
    return output


# ── Main Pipeline ─────────────────────────────────────────────────────────────
def run_biosense(image, description, location_note, language):
    if not image and not description:
        return "⚠️ Please upload an image or enter a description.", ""

    data, raw = identify_species(image, description, location_note, language)
    log_sighting(data, location_note)
    report = format_output(data)
    return report, raw


# ── Gradio UI ─────────────────────────────────────────────────────────────────
def build_ui():
    with gr.Blocks(
        title="BioSense — AI Biodiversity Monitor",
        theme=gr.themes.Soft(primary_hue="green"),
        css="""
        .header { text-align: center; padding: 20px; }
        .tagline { color: #4a7c59; font-style: italic; }
        footer { display: none !important; }
        """
    ) as demo:

        gr.HTML("""
        <div class="header">
            <h1>🌿 BioSense</h1>
            <h3>AI-Powered Biodiversity Monitor for Forest Rangers</h3>
            <p class="tagline">Powered by Gemma 4 · Offline-first · Built for India's Wildlife</p>
        </div>
        """)

        with gr.Row():
            with gr.Column(scale=1):
                image_input = gr.Image(
                    type="filepath",
                    label="📷 Upload Photo (animal, plant, track, or bird)",
                    height=300,
                )
                description_input = gr.Textbox(
                    label="📝 Field Observation (optional)",
                    placeholder="e.g. Large paw print, ~12cm wide, found near waterhole at Ranthambore...",
                    lines=3,
                )
                location_input = gr.Textbox(
                    label="📍 Location Note (optional)",
                    placeholder="e.g. Ranthambore Zone 3, near Malik Talao",
                )
                language_input = gr.Radio(
                    choices=["English", "Hindi", "Rajasthani"],
                    value="English",
                    label="🌐 Output Language",
                )
                identify_btn = gr.Button(
                    "🔍 Identify Species",
                    variant="primary",
                    size="lg",
                )

            with gr.Column(scale=1):
                report_output = gr.Markdown(label="📋 BioSense Report")
                with gr.Accordion("🔧 Raw Model Output (for debugging)", open=False):
                    raw_output = gr.Textbox(label="Raw JSON", lines=10)

        identify_btn.click(
            fn=run_biosense,
            inputs=[image_input, description_input, location_input, language_input],
            outputs=[report_output, raw_output],
        )

        gr.Examples(
            examples=[
                [None, "Large orange and black striped cat, seen near dense grassland, weight approx 180kg", "Ranthambore National Park, Zone 4", "English"],
                [None, "Small brown bird with red beak, hopping on ground near dry shrubs", "Kumbhalgarh Wildlife Sanctuary", "Hindi"],
                [None, "Round paw print, 4 toes, no claw marks, diameter 10cm, found near muddy waterhole", "Sariska Tiger Reserve", "English"],
                [None, "Tall tree with silvery-white bark, large rounded leaves, found near riverbank", "Bandhavgarh National Park", "English"],
            ],
            inputs=[image_input, description_input, location_input, language_input],
            label="📚 Try These Examples",
        )

        gr.HTML("""
        <div style="text-align:center; padding: 15px; color: #666; font-size: 0.85em;">
            BioSense · Built for the Gemma 4 Impact Hackathon · 
            Dedicated to India's 600+ Wildlife Sanctuaries 🐯
        </div>
        """)

    return demo


# ── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    init_log()
    print("🌿 Starting BioSense...")
    print(f"📡 Using model: {MODEL}")
    print("💡 Make sure Ollama is running: ollama serve")
    print(f"💡 Pull the model first: ollama pull {MODEL}")
    demo = build_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
    )
