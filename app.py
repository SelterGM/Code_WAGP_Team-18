# -*- coding: utf-8 -*-

import streamlit as st
import json
import os
from openai import OpenAI

# --------------------------------------------------
# Page Config
# --------------------------------------------------
st.set_page_config(
    page_title="🎓 Path Finder – TH Köln Studien- & Karriereberater",
    layout="wide"
)

# --------------------------------------------------
# Session State
# --------------------------------------------------
if "chat" not in st.session_state:
    st.session_state.chat = []

if "begruesst" not in st.session_state:
    st.session_state.begruesst = False

if "letztes_profil" not in st.session_state:
    st.session_state.letztes_profil = None

if "profil_message_index" not in st.session_state:
    st.session_state.profil_message_index = None

# --------------------------------------------------
# OpenAI Client
# --------------------------------------------------
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# --------------------------------------------------
# Daten laden (UTF-8!)
# --------------------------------------------------
with open("modules_final.json", encoding="utf-8") as f:
    MODULES = json.load(f)

with open("career_profiles.json", encoding="utf-8") as f:
    PROFILES = json.load(f)

with open("pruefungsordnung_clean.json", encoding="utf-8") as f:
    PRUEFUNGSORDNUNG = json.load(f)

# --------------------------------------------------
# System Prompt
# --------------------------------------------------
SYSTEM_PROMPT = """
Du bist ein sachlicher Studien- und Karriereberater
für Studierende der TH Köln (Campus Gummersbach).

Struktur deiner Antworten:
1. Kurze Einordnung der Situation
2. Relevante Zusammenhänge oder Optionen (max. 3–4)
3. Hinweise, worauf man achten kann (neutral, nicht drängend)

Regeln:
- Die Studienphase ist wichtiger als das formale Semester.
- Im Grundstudium keine Spezialisierungs- oder Karrierefestlegung.
- Ruhig, sachlich, beratend formulieren.
"""

# --------------------------------------------------
# Sidebar – Profil
# --------------------------------------------------
st.sidebar.title("Profil")

studiengang = st.sidebar.selectbox(
    "Studiengang",
    [
        "Bitte Studiengang auswählen",
        "Ingenieurwissenschaftliches Grundstudium",
        "Elektrotechnik",
        "Maschinenbau",
        "Wirtschaftsingenieurwesen"
    ]
)

semester = None
if studiengang != "Bitte Studiengang auswählen":
    semester = st.sidebar.slider("Aktuelles Semester", 1, 10, 1)
else:
    st.sidebar.slider("Aktuelles Semester", 1, 10, 1, disabled=True)

im_grundstudium = studiengang == "Ingenieurwissenschaftliches Grundstudium"

schwerpunkt = "Noch kein Schwerpunkt"

if studiengang == "Elektrotechnik":
    schwerpunkt = "Automatisierung (Pflichtschwerpunkt)"

elif studiengang == "Maschinenbau":
    if semester and semester >= 5:
        schwerpunkt = st.sidebar.selectbox(
            "Schwerpunkt", ["Konstruktion", "Fertigung", "Umwelttechnik"]
        )
    else:
        schwerpunkt = "Schwerpunktwahl ab dem 5. Semester"

elif studiengang == "Wirtschaftsingenieurwesen":
    if semester and semester >= 3:
        schwerpunkt = st.sidebar.selectbox(
            "Schwerpunkt", ["Maschinenbau", "Elektrotechnik", "Umwelttechnik"]
        )
    else:
        schwerpunkt = "Schwerpunktwahl ab dem 3. Semester"

# --------------------------------------------------
# Titel
# --------------------------------------------------
st.title("🎓 Path-Finder – KI Studien- & Karriereberater")

# --------------------------------------------------
# Begrüßung
# --------------------------------------------------
if not st.session_state.begruesst:
    st.session_state.chat.append({
        "role": "assistant",
        "content": (
            "Hallo, ich bin **Path Finder** – dein persönlicher KI-Berater "
            "rund um dein Studium und deinen Berufseinstieg an der TH Köln "
            "(Campus Gummersbach).\n\n"
            "Bitte wähle links zuerst deinen Studiengang und dein Semester.\n\n"
            "Ich ersetze **keine** persönliche Beratung, sondern bin eine "
            "**ergänzende Unterstützung**."
        )
    })
    st.session_state.begruesst = True

# --------------------------------------------------
# Profil-Zusammenfassung (eine Nachricht, updatefähig)
# --------------------------------------------------
profil_fertig = studiengang != "Bitte Studiengang auswählen" and semester is not None
aktuelles_profil = (studiengang, semester, schwerpunkt) if profil_fertig else None

if profil_fertig and aktuelles_profil != st.session_state.letztes_profil:
    profil_text = f"""
Alles klar 👍  
Du studierst **{studiengang}**  
und befindest dich im **{semester}. Semester**.

Studienphase: **{"Grundstudium" if im_grundstudium else "Hauptstudium"}**  
Schwerpunkt: **{schwerpunkt}**

Wobei kann ich dich unterstützen?
"""

    if st.session_state.profil_message_index is None:
        st.session_state.chat.append({"role": "assistant", "content": profil_text})
        st.session_state.profil_message_index = len(st.session_state.chat) - 1
    else:
        st.session_state.chat[
            st.session_state.profil_message_index
        ]["content"] = profil_text

    st.session_state.letztes_profil = aktuelles_profil

# --------------------------------------------------
# Chat anzeigen
# --------------------------------------------------
for msg in st.session_state.chat:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --------------------------------------------------
# User Input
# --------------------------------------------------
frage = st.chat_input("Stelle eine Frage zu Studium oder Karriere")
key="chat_input_main"

if frage:
    # 1️⃣ User-Nachricht SOFORT anzeigen
    st.session_state.chat.append({
        "role": "user",
        "content": frage
    })

    with st.chat_message("user"):
        st.markdown(frage)

    # 2️⃣ Messages für OpenAI bauen
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": f"""
Studiengang: {studiengang}
Semester: {semester}
Studienphase: {"Grundstudium" if im_grundstudium else "Hauptstudium"}
Schwerpunkt: {schwerpunkt}
"""}
    ]

    if studiengang in PRUEFUNGSORDNUNG:
        messages.append({
            "role": "system",
            "content": f"""
Relevante Prüfungsordnung für {studiengang}:
{json.dumps(PRUEFUNGSORDNUNG[studiengang], ensure_ascii=False)}
"""
        })

    for msg in st.session_state.chat:
        messages.append(msg)

    # 3️⃣ KI-Antwort holen
    antwort = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.3,
        max_tokens=500
    ).choices[0].message.content

    # 4️⃣ Antwort speichern & anzeigen
    st.session_state.chat.append({
        "role": "assistant",
        "content": antwort
    })

    with st.chat_message("assistant"):
        st.markdown(antwort)
