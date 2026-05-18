BioSense — AI-Powered Biodiversity Monitor

Putting a field biologist in every ranger's pocket — offline, multilingual, and instant.

Built for the Gemma 4 Impact Hackathon | Track: Global Resilience & Safety

The Problem
India is home to 7–8% of the world's biodiversity, spread across 600+ wildlife sanctuaries and national parks. Yet the majority of species sightings go unrecorded — because field documentation is slow, requires experts, and depends on internet connectivity that simply doesn't exist deep in forests like Ranthambore, Kumbhalgarh, or Bandhavgarh.
Forest rangers make life-critical decisions daily: Is this a protected species? How close is too close? Should I alert authorities? — often with no tools, no connectivity, and no expert to call.
BioSense solves this.

🏗️ Architecture
[Camera Input / Photo Upload]
          ↓
[Gemma 4 E4B — Vision + Language (via Ollama)]
          ↓
   ┌──────────────────────────┐
   │ Species Identifier       │ → name, genus, habitat
   │ Threat Assessor          │ → IUCN status, legal flag
   │ Ranger Advisor           │ → recommended action
   │ Sighting Logger          │ → CSV log with timestamp
   └──────────────────────────┘
          ↓
[Gradio UI — works offline on local network]


# Run BioSense
python app.py
Open your browser at http://localhost:7860


🐯 Demo Examples
Try these field observations in the app:

"Large orange and black striped cat, seen near dense grassland, weight approx 180kg" → Ranthambore
"Round paw print, 4 toes, no claw marks, diameter 10cm, near muddy waterhole" → Sariska
"Small brown bird with red beak, hopping on dry shrubs" → Kumbhalgarh
"Tall tree with silvery-white bark, large rounded leaves, near riverbank" → Bandhavgarh


📁 Project Structure
biosense/
├── app.py               # Main Gradio application
├── requirements.txt     # Python dependencies
├── sightings_log.csv    # Auto-generated sighting log
└── README.md


🙏 Acknowledgements

Google DeepMind for Gemma 4
iNaturalist for biodiversity datasets
IUCN Red List for conservation data
Forest Rangers of India 🌿
