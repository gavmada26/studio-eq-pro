# 🎛️ Studio EQ Pro - Hybrid Desktop Audio Player Architecture

This repository contains the complete implementation of an interactive Digital Audio Workstation (DAW) ecosystem designed as a lightweight, non-blocking desktop application using Python and Gradio.

The project bridges the gap between theoretical digital signal processing (DSP) algorithms and real-time studio software. It transforms advanced mathematical operations from offline scripts into a responsive, production-ready audio tool.

The system architecture is inspired by the foundational concepts of [Audio-Equalizer by Ahmed-Hajhamed](https://github.com/Ahmed-Hajhamed/Audio-Equalizer), but has been entirely rewritten, modernized, and significantly extended to feature a complete Frontend/Backend separation, a custom-engineered CSS interface, and professional-grade mastering and spatialization pipelines.

<div align="center">
  <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" width="200" height="200">
    <defs>
      <linearGradient id="eqGrad" x1="0" y1="80" x2="0" y2="20" gradientUnits="userSpaceOnUse">
        <stop offset="0%" stop-color="#0284c7"/>
        <stop offset="50%" stop-color="#2563eb"/>
        <stop offset="100%" stop-color="#00d4ff"/>
      </linearGradient>
    </defs>
    <style>
      .knob1 { animation: k1 3s ease-in-out infinite alternate; }
      .lvl1  { animation: l1 3s ease-in-out infinite alternate; }
      @keyframes k1 { 0%, 100% { transform: translateY(40px); } 50% { transform: translateY(0px); } }
      @keyframes l1 { 0%, 100% { y: 60px; height: 20px; } 50% { y: 20px; height: 60px; } }
      .knob2 { animation: k2 4s ease-in-out infinite alternate; }
      .lvl2  { animation: l2 4s ease-in-out infinite alternate; }
      @keyframes k2 { 0%, 100% { transform: translateY(10px); } 50% { transform: translateY(50px); } }
      @keyframes l2 { 0%, 100% { y: 30px; height: 50px; } 50% { y: 70px; height: 10px; } }
      .knob3 { animation: k3 2.5s ease-in-out infinite alternate; }
      .lvl3  { animation: l3 2.5s ease-in-out infinite alternate; }
      @keyframes k3 { 0%, 100% { transform: translateY(35px); } 50% { transform: translateY(5px); } }
      @keyframes l3 { 0%, 100% { y: 55px; height: 25px; } 50% { y: 25px; height: 55px; } }
    </style>
    <line x1="26" y1="20" x2="26" y2="80" stroke="#1e293b" stroke-width="4" stroke-linecap="round"/>
    <line x1="50" y1="20" x2="50" y2="80" stroke="#1e293b" stroke-width="4" stroke-linecap="round"/>
    <line x1="74" y1="20" x2="74" y2="80" stroke="#1e293b" stroke-width="4" stroke-linecap="round"/>
    <rect class="lvl1" x="23" y="60" width="6" height="20" rx="3" fill="url(#eqGrad)" />
    <rect class="lvl2" x="47" y="30" width="6" height="50" rx="3" fill="url(#eqGrad)" />
    <rect class="lvl3" x="71" y="55" width="6" height="25" rx="3" fill="url(#eqGrad)" />
    <g class="knob1"><rect x="16" y="16" width="20" height="8" rx="2" fill="#ffffff" /></g>
    <g class="knob2"><rect x="40" y="16" width="20" height="8" rx="2" fill="#ffffff" /></g>
    <g class="knob3"><rect x="64" y="16" width="20" height="8" rx="2" fill="#ffffff" /></g>
  </svg>
</div>

---

# ⚙️ System Architecture & Data Flow

The primary engineering goal of **Studio EQ Pro** is to maintain a completely non-blocking, fluid user experience. To achieve this, the system completely decouples the user interface from the heavy mathematical processing core.

While the custom Frontend handles user input, parameters, and display updates, the asynchronous Backend engine executes deep matrix manipulations, Fourier transforms, and fast convolutions in the background via **Librosa** and **SciPy**.

---

## Block Diagram

<div align="center">
  <img src="assets/architecture-diagram.png" alt="Studio EQ Pro Architecture Diagram" width="1000"/>
</div>

---

# ✨ Comprehensive Feature Set

## 1. 10-Band Parametric Equalizer

### Mathematical Core
Utilizes the Short-Time Fourier Transform (STFT) to map time-domain audio signals into the complex frequency domain.

### Gaussian Filtering
Unlike basic brick-wall filters that induce phase distortion and ringing artifacts, this module applies a continuous bell-curve mask (Gaussian distribution) across the target frequencies (31.5 Hz to 16 kHz). This guarantees ultra-smooth spectral transitions and a pristine, natural sound signature.

---

## 2. Real Space (RS) Reverb

### Acoustic Simulation
Emulates real physical spaces (Room, Hall, Chamber, Plate, Cathedral) by generating high-fidelity synthetic Impulse Responses (IR).

### Algorithm
A white noise vector is modulated by a steep, mathematically computed exponential decay envelope matching the selected room's acoustic properties. The raw signal is then processed using Fast Convolution (`scipy.signal.fftconvolve`), optimizing execution speed significantly compared to standard time-domain convolution algorithms.

---

## 3. Wiener Filter & Noise Reduction

### Stationary De-noising
Specifically engineered to combat constant background disturbances such as microphone hiss, system fan noise, or pre-amplifier hum.

### Spectral Tracking
Analyzes the stationary noise floor of the signal, tracks the Signal-to-Noise Ratio (SNR) across individual frequency bins, and subtracts the estimated noise components without introducing musical noise or phase errors.

---

## 4. Dynamics & Mastering (Compressor + Gate)

### Noise Gate
Automatically silences audio sections that drop below a configurable decibel threshold, completely cleansing vocal pauses of ambient artifacts.

### Audio Compressor
Limits high-amplitude transients to achieve a balanced, commercially competitive dynamic range. The compression envelope is driven by exponential smoothing equations governing the automatic Attack (10 ms) and Release (200 ms) curves, preventing digital clipping or sudden volume pumping.

---

## 5. Pitch, Tempo & Echo Engineering

### Independent Manipulation
Allows independent tuning of fundamental frequency (Pitch Shifting) and duration (Time Stretching) without cross-contamination, using a high-quality phase vocoder mechanism.

### Delay Pipeline
Includes an echo module capable of generating recurring, rhythmically clean signal reflections with configurable feedback loops and smooth volume attenuation curves.

---

## 6. Stereo Enhancer (3D Spatial Audio)

### Haas Effect
Widens the perception of the soundstage by creating a precise 15 ms delay vector mapped directly onto the side channel.

### Mid/Side Processing
Separates center mix components from the extreme stereo field.

### Bass Mono Integration
A critical mixing utility that actively intercepts all frequencies below 120 Hz and forces them into a strict mono configuration. This prevents low-frequency phase cancellation, ensuring consistent low-end punch across mono systems, club PAs, and mobile devices.

---

## 7. Interactive Visual Validation

Provides immediate, production-grade visual feedback computed directly from the processed numeric arrays:

### Waveforms
High-resolution rendering of signal amplitude over time.

### Logarithmic Spectrograms
Displays energy distribution matching human auditory perception curves.

### Audiograms
Simulates clinical ORL diagnostic charts, plotting absolute signal intensity across standard reference bands.

---

# 🚀 Installation, Setup, and Execution

To run Studio EQ Pro locally on your machine, follow these structured steps:

## 1. Clone the Repository

```bash
git clone https://github.com/gavmada26/Studio-EQ-Pro.git
cd Studio-EQ-Pro
```
## 2. Create Virtual Environment

It is recommended to isolate dependencies using a virtual environment.

```bash
python -m venv venv
```

Activate the environment:

### Windows (Command Prompt / PowerShell)

```bash
venv\Scripts\activate
```

### macOS / Linux

```bash
source venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 4. Run the Application

```bash
python src/egalizator_gradio.py
```

After launching, the terminal will display the local server address.

Open in browser:

```text
http://127.0.0.1:7860
```

---

## 🎓 Academic Attribution
* **Developer:** Mădălin Gavrilaș
* **Department:** Department of Communications, Faculty of Electronics, Telecommunications and Information Technology (ETTI)
* **Institution:** Technical University of Cluj-Napoca (UTCN), Romania
* **Specialization:** Telecommunications Technologies and Systems (TST-RO)

