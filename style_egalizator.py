# style_egalizator.py

# aici tin tot codul css ca sa nu fac main-ul foarte lung si greu de citit
# practic modific culorile si formele standard de la gradio
CSS_COMPLET = """
/* =========================================
   STILURI GLOBALE (Deep Ocean / Professional Theme)
========================================= */
body, .gradio-container {
    background-color: #070a14 !important; 
    background-image: radial-gradient(circle at 20% 30%, #111827 0%, #070a14 70%) !important;
    color: #e2e8f0;
    font-family: 'Inter', 'Segoe UI', sans-serif !important;
}

/* =========================================
   TIPOGRAFIE & LOGO
========================================= */
.titlu-animat {
    color: #00d4ff !important; 
    text-shadow: 0 0 15px rgba(0, 212, 255, 0.4);
    text-align: center; 
    font-weight: 900;
    padding: 5px 0;
    font-size: 2.8em; 
    letter-spacing: 1px;
    margin: 0 !important;
    text-transform: uppercase;
    line-height: 1.2;
}

/* efect de hover pe logo ca sa stie userul ca se poate da click sa mearga la home */
.titlu-clickabil { text-align: left; font-size: 2.2em; transition: all 0.3s; }
.titlu-clickabil:hover { color: #3b82f6 !important; text-shadow: 0 0 20px rgba(59, 130, 246, 0.8); cursor: pointer; }
.app-logo { height: 1.4em; vertical-align: middle; margin-right: 12px; }

.titlu-sectiune {
    color: #3b82f6 !important; 
    border-bottom: 2px solid #1e293b;
    padding-bottom: 8px;
    margin-bottom: 15px;
    font-weight: 700;
    letter-spacing: 1px;
}

/* stilizare pentru subtitlurile si explicatiile tehnice sa fie mai mari si lizibile */
.desc-efect {
    font-size: 1.15em !important;
    color: #94a3b8 !important;
    font-style: italic;
    line-height: 1.5;
    margin-bottom: 20px !important;
    padding: 10px 15px;
    background: rgba(30, 41, 59, 0.4);
    border-left: 4px solid #3b82f6;
    border-radius: 4px;
}

/* =========================================
   HEADER BADGES
========================================= */
.header-container { display: flex; justify-content: space-between; align-items: center; padding: 15px 25px; }
.badges-container { display: flex; gap: 15px; align-items: center; }

.header-badge { 
    width: 55px; height: 55px; border-radius: 50%; 
    border: 2px solid #00d4ff; cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 0 10px rgba(0, 212, 255, 0.3);
}
.header-badge:hover { transform: scale(1.15) rotate(5deg); box-shadow: 0 0 25px #00d4ff; }

/* =========================================
   BUTOANE PRINCIPALE
========================================= */
button.primary {
    background: linear-gradient(45deg, #2563eb, #00d4ff) !important;
    border: none !important; color: #ffffff !important; border-radius: 6px !important;
    transition: all 0.3s ease !important; text-transform: uppercase; font-weight: 800 !important;
    letter-spacing: 1.5px; box-shadow: 0 0 15px rgba(59, 130, 246, 0.4) !important;
}
button.primary:hover {
    background: linear-gradient(45deg, #00d4ff, #2563eb) !important; 
    box-shadow: 0 0 25px rgba(0, 212, 255, 0.6) !important; transform: scale(1.02);
}

/* =========================================
   SPLASH SCREEN & ANIMATII
========================================= */
@keyframes pulseBackground {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

#splash-screen {
    position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
    background-color: #070a14;
    background-image: radial-gradient(circle at 50% 50%, #111827 0%, #070a14 100%);
    background-size: 200% 200%; animation: pulseBackground 10s ease infinite;
    z-index: 99999; display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    transition: opacity 0.8s cubic-bezier(0.8, 0, 0.2, 1), transform 0.8s cubic-bezier(0.8, 0, 0.2, 1);
    padding: 0 10%;
}

@keyframes floatLogo {
    0% { transform: translateY(0px); filter: drop-shadow(0 0 20px #00d4ff); }
    50% { transform: translateY(-20px); filter: drop-shadow(0 0 40px #3b82f6); }
    100% { transform: translateY(0px); filter: drop-shadow(0 0 20px #00d4ff); }
}

.splash-logo { width: 200px; margin-bottom: 35px; animation: floatLogo 4s ease-in-out infinite; }
.splash-titlu { font-size: 3.5em !important; color: #ffffff !important; text-shadow: 0 0 20px rgba(0, 212, 255, 0.4); max-width: 1000px; }
.splash-subtitlu { color: #94a3b8; font-size: 1.5em; margin-top: 15px; margin-bottom: 50px; font-weight: 500; letter-spacing: 2px; text-align: center; }

.btn-start-anim { 
    background: #00d4ff; border: none; color: #070a14; 
    padding: 20px 55px; font-size: 1.2em; font-weight: 900; border-radius: 6px; 
    cursor: pointer; box-shadow: 0 0 25px rgba(0, 212, 255, 0.4); 
    transition: all 0.3s ease; text-transform: uppercase; letter-spacing: 2px; 
}
.btn-start-anim:hover { background: #2563eb; color: white; box-shadow: 0 0 40px rgba(37, 99, 235, 0.8); transform: scale(1.05); }

#splash-screen.animate-out { 
    animation: fade-out-central 0.8s cubic-bezier(0.4, 0, 0.2, 1) forwards; 
    pointer-events: none; 
}
@keyframes fade-out-central { 
    0% { transform: scale(1); opacity: 1; } 
    100% { transform: scale(1.1); opacity: 0; visibility: hidden; } 
}

#splash-screen.bring-back { 
    animation: fade-in-central 0.8s cubic-bezier(0.4, 0, 0.2, 1) forwards; 
    pointer-events: auto; 
}
@keyframes fade-in-central { 
    0% { transform: scale(1.1); opacity: 0; visibility: hidden; } 
    100% { transform: scale(1); opacity: 1; visibility: visible; } 
}

/* =========================================
   MENIU LATERAL
========================================= */
#tabs_ascunse > div:first-child { display: none !important; }

.titlu-meniu h3 { color: #e2e8f0 !important; padding-left: 10px; font-weight: 800; letter-spacing: 1px; }

.meniu-lateral { background: transparent !important; border: none !important; }
.meniu-lateral .wrap { display: flex !important; flex-direction: column !important; gap: 8px !important; padding: 0 !important; }
.meniu-lateral input[type="radio"] { display: none !important; }

.meniu-lateral label {
    background: #111827 !important; border-radius: 6px !important;
    padding: 15px 20px !important; cursor: pointer !important; transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
    color: #94a3b8 !important; font-weight: 600 !important; text-transform: uppercase; letter-spacing: 1px;
}

.meniu-lateral label:hover { background: #1e293b !important; color: #00d4ff !important; transform: translateX(8px); }

.meniu-lateral label.selected {
    background: linear-gradient(90deg, #2563eb, #00d4ff) !important;
    color: #ffffff !important; font-weight: bold;
    box-shadow: 0 5px 15px rgba(37, 99, 235, 0.4) !important;
}
.meniu-lateral > span { display: none !important; }

/* =========================================
   CONTAINERE, TABEL & SLIDERE
========================================= */
/* am schimbat animatia pe un fade in simplu ca sa nu mai creeze lag la schimbarea taburilor */
@keyframes fadeInSmooth {
    0% { opacity: 0; transform: scale(0.99); }
    100% { opacity: 1; transform: scale(1); }
}

.contain-box {
    background: rgba(15, 23, 42, 0.85) !important;
    backdrop-filter: blur(8px);
    border: 1px solid #1e293b !important;
    border-radius: 8px !important; 
    box-shadow: 0 5px 15px rgba(0,0,0,0.5) !important;
    padding: 20px;
    animation: fadeInSmooth 0.3s ease-out forwards !important;
    transition: border-color 0.3s ease, box-shadow 0.3s ease !important;
}
.contain-box:hover { border-color: #00d4ff !important; box-shadow: 0 10px 25px rgba(0, 212, 255, 0.15) !important; }

/* clasa noua creata special pentru tabelul de la reverb sa arate profesional */
.pro-table table {
    width: 100%; border-collapse: collapse; margin-top: 10px;
    background-color: #0f172a; border-radius: 8px; overflow: hidden;
    border: 1px solid #1e293b;
}
.pro-table th { background-color: #1e293b; color: #00d4ff; padding: 14px; text-align: left; font-weight: 700;}
.pro-table td { padding: 12px 14px; border-bottom: 1px solid #1e293b; color: #cbd5e1; }
.pro-table tr:hover { background-color: #162032; }
.pro-table tr:last-child td { border-bottom: none; }

.toast-wrap { top: auto !important; bottom: 3% !important; left: auto !important; right: 2% !important; z-index: 999999 !important; }
.toast-wrap > div { border-left: 5px solid #00d4ff !important; background: #0f172a !important; color: #ffffff !important; box-shadow: 0 0 20px rgba(0, 212, 255, 0.3) !important; }
input[type=range]::-webkit-slider-thumb { background: #00d4ff !important; box-shadow: 0 0 10px rgba(0, 212, 255, 0.6) !important; }

/* =========================================
   FIX PREVENIRE BLOCAJ ZOOM IMAGINI
========================================= */
button[aria-label="View fullscreen"], 
button[title="View fullscreen"],
.image-button[aria-label="View fullscreen"] {
    display: none !important;
}

.gradio-container .image-frame img,
.gradio-container .image-container img {
    pointer-events: none !important;
}
"""