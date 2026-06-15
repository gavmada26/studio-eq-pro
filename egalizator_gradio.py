# import librariile de sistem pentru lucrul cu fisiere si cai
import sys
import os

# ocolesc eroarea de windows care pica serverul cand se intrerupe conexiunea pipe
if sys.platform == 'win32':
    try:
        from asyncio.proactor_events import _ProactorBasePipeTransport

        def silence_winerror_10054(func):
            def wrapper(self, *args, **kwargs):
                try:
                    return func(self, *args, **kwargs)
                except ConnectionResetError:
                    pass

            return wrapper

        _ProactorBasePipeTransport._call_connection_lost = silence_winerror_10054(
            _ProactorBasePipeTransport._call_connection_lost)
    except Exception:
        pass

# import gradio pentru interfata web si backendul de procesare
import gradio as gr
import base64
from style_egalizator import CSS_COMPLET
from eq_backend import StudioDSP

# instantiez clasa dsp care se va ocupa de toata matematica sunetului
dsp = StudioDSP()
# setez tema de baza pe care o suprascriu oricum in css mai tarziu
tema_moderna = gr.themes.Default(primary_hue="blue", neutral_hue="slate")

# generez un logo animat cu svg ca sa nu folosesc poze grele si sa se vada clar pe orice ecran
logo_svg_code = """
<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
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
  <rect class="lvl2" x="47" y="20" width="6" height="50" rx="3" fill="url(#eqGrad)" />
  <rect class="lvl3" x="71" y="55" width="6" height="25" rx="3" fill="url(#eqGrad)" />
  <g class="knob1"><rect x="16" y="16" width="20" height="8" rx="2" fill="#ffffff" /></g>
  <g class="knob2"><rect x="40" y="16" width="20" height="8" rx="2" fill="#ffffff" /></g>
  <g class="knob3"><rect x="64" y="16" width="20" height="8" rx="2" fill="#ffffff" /></g>
</svg>
"""
# transform codul svg in string de tip base64 ca sa il poata randa html-ul direct
LOGO_BASE64 = "data:image/svg+xml;base64," + base64.b64encode(logo_svg_code.encode('utf-8')).decode('utf-8')

# ─── MENIU NAVIGARE ────────────────────────────────────────────────────────────
# definesc structura meniului principal din stanga
PAGINI = [
    "🎛️ EGALIZATOR STANDARD",
    "🌊 RS REVERB",
    "🧹 WIENER FILTER & NOISE",
    "🎚️ DINAMICĂ & MASTERING",
    "⏱️ PITCH, TEMPO & ECOU",
    "🔊 STEREO ENHANCER",
    "📈 SPECTOGRAMĂ & DSP"
]

# ascund output-urile pana cand e gata piesa de incarcat
def incarca_si_ascunde_rezultatele(fisier_audio, preview_mode):
    if fisier_audio is None:
        return gr.update(visible=False), None, None
    # setez un mesaj dinamic in functie de ce a bifat utilizatorul
    msg = "⏳ Se încarcă primele 30 secunde (Fast Preview)..." if preview_mode else "⏳ Se încarcă fișierul audio complet..."
    gr.Info(msg, duration=3)

    # incarc efectiv piesa in ram
    succes = dsp.load_audio(fisier_audio, preview_mode=preview_mode)
    if succes:
        gr.Info("✅ Fișier pregătit! Efectuează reglajele și apasă PROCESEAZĂ.", duration=3)
        spec_in = dsp.plot_spectrogram(dsp.y_orig, "Spectrogramă Originală")
        audio_in_img = dsp.plot_audiogram(dsp.y_orig)
        return gr.update(visible=False), spec_in, audio_in_img
    return gr.update(visible=False), None, None


# functie care face switch intre taburi pe baza selectiei din radio button
def schimba_tab_din_meniu(selectie):
    mapare_taburi = {
        "🎛️ EGALIZATOR STANDARD": "tab_rack",
        "🌊 RS REVERB": "tab_reverb",
        "🧹 WIENER FILTER & NOISE": "tab_wiener",
        "🎚️ DINAMICĂ & MASTERING": "tab_dinamica",
        "⏱️ PITCH, TEMPO & ECOU": "tab_timp",
        "🔊 STEREO ENHANCER": "tab_stereo",
        "📈 SPECTOGRAMĂ & DSP": "tab_analiza",
    }
    return gr.update(selected=mapare_taburi.get(selectie, "tab_rack"))


# ─── HANDLERE PROCESARE ────────────────────────────────────────────────────────

# trimite datele sliderelor catre egalizatorul parametric
def proceseaza_eq_standard(fisier_audio, preview_mode, b1, b2, b3, b4, b5, b6, b7, b8, b9, b10, widener, reverb, drive):
    if fisier_audio is None: raise gr.Error("Te rog încarcă un fișier audio mai întâi!", duration=3)
    gr.Info("⏳ Procesare STFT (EQ Standard)...", duration=3)
    dsp.load_audio(fisier_audio, preview_mode=preview_mode)
    gains = [b1, b2, b3, b4, b5, b6, b7, b8, b9, b10]
    y_final = dsp.process_audio(gains, widener, reverb, drive)
    return randare_interfata_generala(y_final)

def proceseaza_reverb(fisier_audio, preview_mode, preset, intensity):
    # trimite setarile catre modulul convolutiv
    if fisier_audio is None: raise gr.Error("Te rog încarcă un fișier audio mai întâi!", duration=3)
    gr.Info(f"⏳ Aplicare RS Reverb preset «{preset}»...", duration=3)
    dsp.load_audio(fisier_audio, preview_mode=preview_mode)
    y_final = dsp.process_reverb(preset=preset, intensity=intensity)
    return randare_interfata_generala(y_final)

def proceseaza_wiener(fisier_audio, preview_mode, alpha):
    if fisier_audio is None: raise gr.Error("Te rog încarcă un fișier audio mai întâi!", duration=3)
    gr.Info("⏳ Aplicare filtru Wiener (Reducere zgomot)...", duration=3)
    dsp.load_audio(fisier_audio, preview_mode=preview_mode)
    y_final = dsp.process_wiener(alpha)
    return randare_interfata_generala(y_final)

def proceseaza_dinamica(fisier_audio, preview_mode, comp_thresh, comp_ratio, gate_thresh, makeup_gain):
    if fisier_audio is None: raise gr.Error("Te rog încarcă un fișier audio mai întâi!", duration=3)
    gr.Info("⏳ Procesare Compresor & Noise Gate...", duration=3)
    dsp.load_audio(fisier_audio, preview_mode=preview_mode)

    # incarc intai gate-ul ca sa curat linistea inainte sa comprimam
    y_gated = dsp.process_noise_gate(threshold_db=gate_thresh)
    dsp.y_orig = y_gated  # salvez intermediar ca sa preia compresorul semnalul deja curatat
    y_final = dsp.process_dynamics(threshold_db=comp_thresh, ratio=comp_ratio, makeup_gain=makeup_gain)
    dsp.y_orig = dsp.y_orig if dsp.y_orig is not None else y_final  # restaurez starea initiala in memorie
    return randare_interfata_generala(y_final)

def proceseaza_timp(fisier_audio, preview_mode, pitch_steps, fine_cents, stretch_rate, delay_ms, delay_fb, delay_mix):
    if fisier_audio is None: raise gr.Error("Te rog încarcă un fișier audio mai întâi!", duration=3)
    gr.Info("⏳ Modificare pitch, tempo și ecou...", duration=3)
    dsp.load_audio(fisier_audio, preview_mode=preview_mode)

    # ajustez tonalitatea intai ca sa nu distorsioneze ecoul
    y_pitched = dsp.process_pitch_tempo(
        pitch_semitones=pitch_steps,
        fine_cents=fine_cents,
        tempo_rate=stretch_rate
    )

    # aplic delay-ul dupa pitch doar daca valoarea de ms este mai mare de zero
    if delay_ms > 0:
        dsp.y_orig = y_pitched
        y_final = dsp.process_delay(delay_ms=delay_ms, feedback=delay_fb, mix=delay_mix)
    else:
        y_final = y_pitched

    return randare_interfata_generala(y_final)

def proceseaza_stereo(fisier_audio, preview_mode, width, bass_mono_freq, side_gain):
    if fisier_audio is None: raise gr.Error("Te rog încarcă un fișier audio mai întâi!", duration=3)
    gr.Info("⏳ Aplicare Stereo Enhancer (3D Audio)...", duration=3)
    dsp.load_audio(fisier_audio, preview_mode=preview_mode)
    y_final = dsp.process_stereo_enhancer(width=width, bass_mono_freq=int(bass_mono_freq), side_gain=side_gain)
    return randare_interfata_generala(y_final)

# metoda generalizata care e chemata de orice buton pt a actualiza graficele in pagina
def randare_interfata_generala(y_final):
    wave_img = dsp.plot_waveform(y_final, "Undă Procesată", "#00d4ff")
    spec_img = dsp.plot_spectrogram(y_final, "Spectrogramă Procesată")
    audiogram_img = dsp.plot_audiogram(y_final)
    fisier_export = dsp.export_wav(y_final)
    gr.Info("✅ Procesare completă cu succes!", duration=3)
    return gr.update(visible=True), fisier_export, wave_img, spec_img, audiogram_img


# ─── UI GRADIO ─────────────────────────────────────────────────────────────────
# incep block-ul principal de randare a paginii
with gr.Blocks(title="Studio EQ Pro") as interfata:
    # incarc un html brut pentru ecranul de loading (splash screen)
    gr.HTML(f"""
    <div id="splash-screen">
    <img src="{LOGO_BASE64}" class="splash-logo" alt="Logo Proiect">
    <h1 class='titlu-animat splash-titlu'>STUDIO EQ PRO</h1>
    <div class='splash-subtitlu'>Digital Audio Workstation & DSP</div>
    <button class="btn-start-anim" onclick="
    let splash = document.getElementById('splash-screen');
    splash.classList.remove('bring-back');
    splash.classList.add('animate-out');
    ">INIȚIALIZARE APLICAȚIE</button>
    </div>
    """)

    # antetul site-ului permanent care ramane sus
    gr.HTML(f"""
    <div class="header-container">
        <h1 class='titlu-animat titlu-clickabil' onclick="
        let splash = document.getElementById('splash-screen');
        splash.classList.remove('animate-out');
        splash.classList.add('bring-back');
        ">
        <img src="{LOGO_BASE64}" class="app-logo"> STUDIO EQ PRO
        </h1>
    </div>
    """)

    with gr.Row():
        with gr.Column(scale=2):
            gr.Markdown("### NAVIGARE DSP", elem_classes="titlu-meniu")
            meniu_nav = gr.Radio(
                choices=PAGINI,
                value=PAGINI[0],
                label="",
                elem_classes="meniu-lateral",
                interactive=True
            )

        with gr.Column(scale=9):
            with gr.Column(elem_classes="contain-box"):
                gr.Markdown("### 📥 INTRARE SEMNAL AUDIO", elem_classes="titlu-sectiune")
                audio_in = gr.Audio(
                    label="Încarcă Piesa (WAV/MP3)",
                    type="filepath"
                )
                chk_preview = gr.Checkbox(
                    label="⚡ Fast Preview Mode (Activează pentru procesare rapidă: decupează la primele 30 sec)",
                    value=True, interactive=True
                )

            # folosesc componenta de tabs ascunsa pt tranzitiile dintre unelte
            with gr.Tabs(elem_id="tabs_ascunse", selected="tab_rack") as element_tabs:
                # ── TAB 1: EGALIZATOR STANDARD ─────────────────────────────────
                with gr.TabItem("🎛️ EGALIZATOR STANDARD", id="tab_rack"):
                    with gr.Row():
                        with gr.Column(scale=3, elem_classes="contain-box"):
                            gr.Markdown("### 🎛️ EFECTE SPAȚIALE", elem_classes="titlu-sectiune")
                            slider_widener = gr.Slider(minimum=0.0, maximum=2.0, value=1.0, step=0.1,
                                                       label="Lățime Stereo (Widener)")
                            slider_reverb = gr.Slider(minimum=0.0, maximum=1.0, value=0.0, step=0.05,
                                                      label="Mixaj Reverb")
                            slider_drive = gr.Slider(minimum=0.5, maximum=3.0, value=1.0, step=0.1,
                                                     label="Saturație (Tube Drive)")

                        with gr.Column(scale=9, elem_classes="contain-box"):
                            gr.Markdown("### 🎚️ EGALIZATOR GRAFIC (10 Benzi)", elem_classes="titlu-sectiune")
                            with gr.Row():
                                b1 = gr.Slider(minimum=-12, maximum=12, value=0, step=0.5, label="31 Hz")
                                b2 = gr.Slider(minimum=-12, maximum=12, value=0, step=0.5, label="62 Hz")
                                b3 = gr.Slider(minimum=-12, maximum=12, value=0, step=0.5, label="125 Hz")
                                b4 = gr.Slider(minimum=-12, maximum=12, value=0, step=0.5, label="250 Hz")
                                b5 = gr.Slider(minimum=-12, maximum=12, value=0, step=0.5, label="500 Hz")
                            with gr.Row():
                                b6 = gr.Slider(minimum=-12, maximum=12, value=0, step=0.5, label="1 kHz")
                                b7 = gr.Slider(minimum=-12, maximum=12, value=0, step=0.5, label="2 kHz")
                                b8 = gr.Slider(minimum=-12, maximum=12, value=0, step=0.5, label="4 kHz")
                                b9 = gr.Slider(minimum=-12, maximum=12, value=0, step=0.5, label="8 kHz")
                                b10 = gr.Slider(minimum=-12, maximum=12, value=0, step=0.5, label="16 kHz")
                            btn_proceseaza_eq = gr.Button("⚙️ APLICĂ EGALIZATOR STANDARD", variant="primary", size="lg")

                # ── TAB 2: RS REVERB ────────────
                with gr.TabItem("🌊 RS REVERB", id="tab_reverb"):
                    with gr.Column(elem_classes="contain-box"):
                        gr.Markdown("### 🌊 RS REVERB ", elem_classes="titlu-sectiune")
                        gr.Markdown(
                            "Procesare spațială avansată bazată pe răspuns la impuls (IR). "
                            "Simulează reflexiile acustice specifice diverselor incinte la nivel de studio.",
                            elem_classes="desc-efect"
                        )
                        with gr.Row():
                            s_reverb_preset = gr.Dropdown(
                                choices=["Room", "Hall", "Chamber", "Plate", "Cathedral"],
                                value="Room",
                                label="🏛️ Model Acustic (Preset)"
                            )
                            s_reverb_intensity = gr.Slider(
                                minimum=0.0, maximum=2.0, value=1.0, step=0.05,
                                label="💧 Mixaj Reverb (Dry/Wet) - Intensitate efect"
                            )
                        # am adaugat clasa pro-table pe elementul de markdown care genereaza tabelul
                        gr.Markdown("""
| Preset | Dimensiune | Timp de stingere (Decay) | Caracteristici Acustice |
|--------|------------|--------------------------|-------------------------|
| Room | Mică | Scurt | Spații intime, util pentru prezență vocală naturală |
| Hall | Medie | Mediu | Săli de concert clasice, dispersie acustică uniformă |
| Chamber | Medie | Mediu | Camere de reverberație de studio, sunet dens |
| Plate | N/A | Mediu | Reverberație mecanică (placă metalică), excelent pentru percuție |
| Cathedral | Masivă | Foarte Lung | Spații arhitecturale enorme, ideal pentru design sonor și ambient |
                        """, elem_classes="pro-table")
                        btn_proceseaza_reverb = gr.Button("⚙️ APLICĂ RS REVERB", variant="primary", size="lg")

                # ── TAB 3: WIENER FILTER ───────────────────────────────────────
                with gr.TabItem("🧹 WIENER FILTER & NOISE", id="tab_wiener"):
                    with gr.Column(elem_classes="contain-box"):
                        gr.Markdown("### 🧹 WIENER NOISE REDUCTION", elem_classes="titlu-sectiune")
                        s_alpha = gr.Slider(minimum=0, maximum=1000, value=100, step=10,
                                            label="Coeficient de Reducere (Alpha)")
                        btn_proceseaza_wiener = gr.Button("⚙️ APLICĂ FILTRU WIENER", variant="primary", size="lg")

                # ── TAB 4: DINAMICĂ & MASTERING ────────────────────────────────
                with gr.TabItem("🎚️ DINAMICĂ & MASTERING", id="tab_dinamica"):
                    with gr.Column(elem_classes="contain-box"):
                        gr.Markdown("### 🗜️ COMPRESOR + NOISE GATE ", elem_classes="titlu-sectiune")
                        gr.Markdown(
                            "Control avansat al gamei dinamice. Algoritm de compresie cu netezire exponențială "
                            "(Attack automat 10ms / Release automat 200ms) precedat de o poartă de zgomot (Noise Gate).",
                            elem_classes="desc-efect"
                        )
                        gr.Markdown("#### 🔇 Noise Gate", elem_classes="titlu-sectiune")
                        with gr.Row():
                            s_gate = gr.Slider(minimum=-80, maximum=0, value=-80, step=1,
                                               label="Prag Noise Gate (dB) - Anulează semnalul sub acest nivel")
                        gr.Markdown("#### 🗜️ Compresor", elem_classes="titlu-sectiune")
                        with gr.Row():
                            s_comp_thresh = gr.Slider(minimum=-60, maximum=0, value=-20, step=1,
                                                      label="Prag Compresor (Threshold în dB)")
                            s_comp_ratio = gr.Slider(minimum=1.0, maximum=20.0, value=1.0, step=0.5,
                                                     label="Rata de Compresie (Ratio X:1)")
                            s_makeup = gr.Slider(minimum=0, maximum=24, value=0, step=0.5,
                                                 label="Câștig de Compensare (Make-Up Gain în dB)")
                        btn_proceseaza_dinamica = gr.Button("⚙️ APLICĂ GATE + COMPRESOR", variant="primary", size="lg")

                # ── TAB 5: PITCH, TEMPO & ECHO ─────────────────────────────────
                with gr.TabItem("⏱️ PITCH, TEMPO & ECOU", id="tab_timp"):
                    with gr.Column(elem_classes="contain-box"):
                        gr.Markdown("### 🎵 PITCH SHIFTER", elem_classes="titlu-sectiune")
                        gr.Markdown(
                            "Ajustare independentă a frecvenței fundamentale (Pitch Shift) și a vitezei de redare (Time Stretch). "
                            "Permite control fin la nivel de cenți (1 semiton = 100 cenți).",
                            elem_classes="desc-efect"
                        )
                        with gr.Row():
                            s_pitch = gr.Slider(minimum=-12, maximum=12, value=0, step=1,
                                                label="Modificare Tonalitate (Semitonuri)")
                            s_fine_cents = gr.Slider(minimum=-100, maximum=100, value=0, step=1,
                                                     label="Acordaj Fin (Cenți)")
                            s_stretch = gr.Slider(minimum=0.5, maximum=2.0, value=1.0, step=0.1,
                                                  label="Modificator Viteză (0.5 = lent, 2.0 = rapid)")

                        gr.Markdown("### 🕳️ DELAY & ECOU", elem_classes="titlu-sectiune")
                        with gr.Row():
                            s_delay_ms = gr.Slider(minimum=0, maximum=2000, value=0, step=10,
                                                   label="Timp Întârziere (Delay Time în ms)")
                            s_delay_fb = gr.Slider(minimum=0.0, maximum=0.9, value=0.3, step=0.05,
                                                   label="Nivel de Repetiție (Feedback)")
                            s_delay_mix = gr.Slider(minimum=0.0, maximum=1.0, value=0.3, step=0.05,
                                                    label="Echilibru Semnal (Dry/Wet Mix)")

                        btn_proceseaza_timp = gr.Button("⚙️ APLICĂ PITCH & ECOU", variant="primary", size="lg")

                # ── TAB 6: STEREO ENHANCER ───────────────────────────────
                with gr.TabItem("🔊 STEREO ENHANCER", id="tab_stereo"):
                    with gr.Column(elem_classes="contain-box"):
                        gr.Markdown("### 🔊 STEREO ENHANCER — 3D Audio", elem_classes="titlu-sectiune")
                        gr.Markdown(
                            "Procesare Mid/Side combinată cu efect Haas (întârziere 15ms) pentru expansiunea imaginii stereo, "
                            "incluzând filtru activ pentru centrarea frecvențelor joase (Bass Mono) și menținerea impactului sonor.",
                            elem_classes="desc-efect"
                        )
                        with gr.Row():
                            s_width = gr.Slider(minimum=0.0, maximum=3.0, value=1.0, step=0.1,
                                                label="Lățime Stereo (0 = mono, 1 = normal, 3 = extra-larg)")
                            s_bass_mono = gr.Slider(minimum=20, maximum=300, value=120, step=10,
                                                    label="Frecvență Bass Mono (Hz) - Sub acest prag semnalul rămâne central")
                            s_side_gain = gr.Slider(minimum=0.0, maximum=2.0, value=1.0, step=0.1,
                                                    label="Câștig Lateral (Amplitudine canal Side)")
                        btn_proceseaza_stereo = gr.Button("⚙️ APLICĂ STEREO ENHANCER", variant="primary", size="lg")

                # ── TAB 7: AUDIOGRAMĂ & DSP ────────────────────────────────────
                with gr.TabItem("📈 AUDIOGRAMĂ & DSP", id="tab_analiza"):
                    with gr.Row():
                        with gr.Column(elem_classes="contain-box"):
                            gr.Markdown("### 📊 SPECTROGRAME", elem_classes="titlu-sectiune")
                            spec_in = gr.Image(label="Original", interactive=False)
                            spec_out = gr.Image(label="Procesat", interactive=False)
                        with gr.Column(elem_classes="contain-box"):
                            gr.Markdown("### 📈 AUDIOGRAME", elem_classes="titlu-sectiune")
                            audiogram_in = gr.Image(label="Audiogramă Originală", interactive=False)
                            audiogram_out = gr.Image(label="Audiogramă Procesată", interactive=False)

            # zona in care scot rezultatul dupa ce user-ul proceseaza. apare abia dupa executie
            with gr.Column(visible=False) as master_rezultate_col:
                gr.Markdown("### 🎧 IEȘIRE MASTER", elem_classes="titlu-sectiune")
                audio_out = gr.Audio(
                    label="Semnal Procesat",
                    interactive=False,
                    waveform_options=gr.WaveformOptions(waveform_color="#3b82f6")
                )
                wave_out = gr.Image(label="Undă Post-Procesare", interactive=False)

    # ─── LEGAREA EVENIMENTELOR PENTRU INTERFATA ─────────────────────────────────────────────────

    # ascult pe selectia meniului ca sa schimb interfata in dreapta
    meniu_nav.change(fn=schimba_tab_din_meniu, inputs=[meniu_nav], outputs=[element_tabs])

    # triggere care pornesc procesarea din backend si actualizeaza UI-ul cand sunt gata
    audio_in.change(
        fn=incarca_si_ascunde_rezultatele,
        inputs=[audio_in, chk_preview],
        outputs=[master_rezultate_col, spec_in, audiogram_in]
    )

    btn_proceseaza_eq.click(
        fn=proceseaza_eq_standard,
        inputs=[audio_in, chk_preview, b1, b2, b3, b4, b5, b6, b7, b8, b9, b10,
                slider_widener, slider_reverb, slider_drive],
        outputs=[master_rezultate_col, audio_out, wave_out, spec_out, audiogram_out]
    )

    btn_proceseaza_reverb.click(
        fn=proceseaza_reverb,
        inputs=[audio_in, chk_preview, s_reverb_preset, s_reverb_intensity],
        outputs=[master_rezultate_col, audio_out, wave_out, spec_out, audiogram_out]
    )

    btn_proceseaza_wiener.click(
        fn=proceseaza_wiener,
        inputs=[audio_in, chk_preview, s_alpha],
        outputs=[master_rezultate_col, audio_out, wave_out, spec_out, audiogram_out]
    )

    btn_proceseaza_dinamica.click(
        fn=proceseaza_dinamica,
        inputs=[audio_in, chk_preview, s_comp_thresh, s_comp_ratio, s_gate, s_makeup],
        outputs=[master_rezultate_col, audio_out, wave_out, spec_out, audiogram_out]
    )

    btn_proceseaza_timp.click(
        fn=proceseaza_timp,
        inputs=[audio_in, chk_preview, s_pitch, s_fine_cents, s_stretch, s_delay_ms, s_delay_fb, s_delay_mix],
        outputs=[master_rezultate_col, audio_out, wave_out, spec_out, audiogram_out]
    )

    btn_proceseaza_stereo.click(
        fn=proceseaza_stereo,
        inputs=[audio_in, chk_preview, s_width, s_bass_mono, s_side_gain],
        outputs=[master_rezultate_col, audio_out, wave_out, spec_out, audiogram_out]
    )

# pornirea efectiva a aplicatiei
if __name__ == "__main__":
    print("[sistem] Studio EQ Pro pornit...")
    interfata.launch(server_name="127.0.0.1", inbrowser=True, theme=tema_moderna, css=CSS_COMPLET)