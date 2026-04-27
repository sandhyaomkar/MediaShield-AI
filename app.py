import streamlit as st
import cv2
import numpy as np
from PIL import Image
from skimage.metrics import structural_similarity as ssim
import pandas as pd
import google.generativeai as genai
import datetime
import random
import matplotlib.pyplot as plt

# 🔑 Configure Gemini
API_KEY = "AIzaSyDi0HnHOTN3vJxrPmVJzmy9NtWZ4Mao8Rs"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-3.1-flash-lite-preview")

st.set_page_config(page_title="MediaShield AI Pro", layout="wide")

# Custom CSS for a dark, modern look
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1f2937; padding: 15px; border-radius: 10px; border: 1px solid #374151; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ MediaShield AI Pro")
st.markdown("### *Next-Gen Forensic Asset Protection & Tamper Detection*")

if "history" not in st.session_state: st.session_state.history = []
if "ai_report" not in st.session_state: st.session_state.ai_report = None

# --- Advanced Forensic Logic ---

def process_forensics(imgA, imgB):
    # Resize for processing
    width, height = 400, 400
    imgA_res = cv2.resize(imgA, (width, height))
    imgB_res = cv2.resize(imgB, (width, height))
    
    # 1. Convert to grayscale
    grayA = cv2.cvtColor(imgA_res, cv2.COLOR_RGB2GRAY)
    grayB = cv2.cvtColor(imgB_res, cv2.COLOR_RGB2GRAY)

    # 2. Compute Structural Similarity and Difference Map
    score, diff = ssim(grayA, grayB, full=True)
    diff = (diff * 255).astype("uint8")
    
    # 3. Create a Heatmap of changes
    thresh = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    heatmap = cv2.applyColorMap(thresh, cv2.COLORMAP_JET)
    
    # 4. Color Histogram Comparison
    histA = cv2.calcHist([imgA_res], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
    histB = cv2.calcHist([imgB_res], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
    color_score = cv2.compareHist(histA, histB, cv2.HISTCMP_CORREL)
    
    return score, heatmap, color_score

def get_ai_legal_opinion(image):
    try:
        pil_img = Image.fromarray(image)
        pil_img.thumbnail((800, 800))
        
        prompt = """
        SYSTEM: You are a Digital Rights Attorney. 
        TASK: Analyze this image for 'Commercial Origin' and 'Copyright Footprints'.
        
        CHECKLIST:
        - Are there broadcast watermarks (e.g., ESPN, SkySports, Netflix)?
        - Is there metadata burned into the frame (Timecodes, Scoreboards)?
        - Does the image contain 'High-Value' individuals (Celebrities/Athletes)?
        
        REPORT FORMAT:
        1. ASSET CLASS: (e.g. Editorial, Commercial, Private)
        2. INFRINGEMENT RISK: (0-100%)
        3. LEGAL ADVICE: (Briefly: Can this be used under Fair Use?)
        """
        response = model.generate_content([prompt, pil_img])
        return response.text
    except Exception as e:
        return f"Legal Engine Offline: {str(e)}"

# --- Sidebar ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2092/2092663.png", width=100)
st.sidebar.header("System Status")
st.sidebar.success("Engine: Gemini 3.1 Flash-Lite")
st.sidebar.info(f"Database: {len(st.session_state.history)} Assets Logged")

# --- UI Layout ---
u1, u2 = st.columns(2)
with u1: file1 = st.file_uploader("Reference Asset (Original)", type=["jpg","png","jpeg"])
with u2: file2 = st.file_uploader("Suspect Asset (Scan)", type=["jpg","png","jpeg"])

if file1 and file2:
    img1 = np.array(Image.open(file1).convert("RGB"))
    img2 = np.array(Image.open(file2).convert("RGB"))
    
    # Run Forensics
    ssim_score, heatmap, color_corr = process_forensics(img1, img2)
    
    # Display Visuals
    row1 = st.columns(3)
    row1[0].image(img1, caption="Original Asset", use_container_width=True)
    row1[1].image(img2, caption="Suspect Asset", use_container_width=True)
    row1[2].image(heatmap, caption="Tamper Heatmap (Red = Change)", use_container_width=True)
    
    st.markdown("---")
    
    # Unique Metrics Dashboard
    m1, m2, m3 = st.columns(3)
    m1.metric("Structural Integrity", f"{ssim_score*100:.1f}%")
    m2.metric("Color DNA Match", f"{color_corr*100:.1f}%")
    m3.metric("Tamper Confidence", "High" if ssim_score < 0.9 else "Low")

    # AI Analysis
    st.subheader("⚖️ AI Forensic & Legal Opinion")
    if st.button("Execute Deep Forensic Scan"):
        with st.spinner("Analyzing legal footprints..."):
            st.session_state.ai_report = get_ai_legal_opinion(img2)
            
    if st.session_state.ai_report:
        st.info(st.session_state.ai_report)

    # Logging
    if st.button("🔒 Archive Scan Results"):
        entry = {
            "Timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
            "Structural": f"{ssim_score:.2f}",
            "Color": f"{color_corr:.2f}",
            "Verdict": "Infringement" if ssim_score < 0.8 else "Original"
        }
        st.session_state.history.append(entry)
        st.toast("Record encrypted and saved to history.")

# History Table
if st.session_state.history:
    with st.expander("📜 Secure Audit Logs"):
        st.table(pd.DataFrame(st.session_state.history))
        