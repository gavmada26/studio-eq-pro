# import librariile matematice pentru lucrul cu matrici si procesare de semnal
import numpy as np
import librosa
import librosa.display
import soundfile as sf
import tempfile
import noisereduce as nr
import matplotlib
from scipy.fft import rfft, rfftfreq
from scipy.signal import fftconvolve

# ascund niste avertismente (warnings) de la python
# ele apar cand se face logaritm din zero, e o chestie matematica normala in dsp
import warnings

warnings.filterwarnings("ignore", message="divide by zero encountered in log10")
warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*divide by zero.*")

# oblig matplotlib sa mearga in fundal (fara interfata grafica a lui) ca sa nu dea eroare pe server
matplotlib.use('Agg')
import matplotlib.pyplot as plt


# definesc clasa principala care se ocupa de tot creierul aplicatiei
class StudioDSP:
    def __init__(self):
        # setez calitatea standard de cd a sunetului la 44.1 khz
        self.sr = 44100
        # aici voi tine in memorie piesa bruta dupa ce o incarc
        self.y_orig = None
        # salvez calea fisierului ca sa nu il incarc de doua ori degeaba
        self.last_file = None
        self.is_preview = None

    # functie care incarca fisierul audio pe baza caii primite de la gradio
    def load_audio(self, file_path, preview_mode=False, preview_duration=30):
        # daca nu e niciun fisier, opresc executia
        if not file_path: return False

        # verific daca fisierul e deja in memorie cu aceleasi setari ca sa economisesc timp
        if self.last_file == file_path and self.y_orig is not None and self.is_preview == preview_mode:
            return True

        # librosa incarca sunetul si il transforma intr-un array lung de numere (y) mono
        y, sr = librosa.load(file_path, sr=self.sr, mono=True)

        # daca userul vrea doar previzualizare rapida, tai semnalul la 30 secunde
        if preview_mode:
            max_samples = int(preview_duration * sr)
            if len(y) > max_samples:
                y = y[:max_samples]

        # actualizez starea interna a clasei cu noul fisier si datele lui
        self.y_orig = y
        self.last_file = file_path
        self.is_preview = preview_mode
        return True

    # =========================================================
    # 1. EGALIZATOR STANDARD (Menținut)
    # =========================================================
    # modifica frecventele folosind stft si adauga putina distorsiune "tube"
    def process_audio(self, gains, widener=1.0, reverb_mix=0.0, drive=1.0):
        if self.y_orig is None: return None
        y = self.y_orig.copy()

        # daca aplic saturatie, folosesc functia tanh ca sa curbez varfurile de volum muzical
        if drive != 1.0:
            y = np.tanh(y * drive) / np.tanh(drive)

        # cele 10 benzi standard ale unui egalizator grafic
        freqs = [31.5, 63, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]
        # trec din domeniul timpului in domeniul frecventei ca sa umblu la ele
        S = librosa.stft(y)
        S_mag, S_phase = librosa.magphase(S)
        fft_freqs = librosa.fft_frequencies(sr=self.sr)

        # parcurg fiecare banda de frecventa si o amplific/tai conform slidere-lor
        for i, target_f in enumerate(freqs):
            gain_linear = 10 ** (gains[i] / 20)
            if gain_linear == 1.0: continue
            # creez o curba fina tip clopot (gaussiana) ca tranzitia sa fie neteda intre frecvente
            band_mask = np.exp(-0.5 * ((fft_freqs - target_f) / (target_f * 0.5)) ** 2)
            S_mag *= (1.0 + (gain_linear - 1.0) * band_mask[:, np.newaxis])

        # recompun fisierul combinand magnitudinea modificata cu faza originala
        S_modified = S_mag * S_phase
        y_out = librosa.istft(S_modified)  # trec inapoi din frecventa in timp

        # un mic truc pentru un ecou foarte ieftin aplicat direct daca e cerut
        if reverb_mix > 0:
            reverb_sig = np.roll(y_out, int(self.sr * 0.05)) * 0.5 + np.roll(y_out, int(self.sr * 0.1)) * 0.25
            y_out = (1 - reverb_mix) * y_out + reverb_mix * reverb_sig

        self.y_proc = y_out
        return y_out

    # =========================================================
    # 2. RS REVERB (înlocuiește Animals & Vocals – Effetune)
    #    Convoluție cu IR sintetic bazat pe preset
    # =========================================================
    # dictionar in care tin preseturile incaperilor, cu dimensiuni si timpi de stingere diferiti
    REVERB_PRESETS = {
        "Room": {"size": 0.20, "decay": 0.30, "wet": 0.30},
        "Hall": {"size": 0.50, "decay": 0.60, "wet": 0.40},
        "Chamber": {"size": 0.35, "decay": 0.50, "wet": 0.35},
        "Plate": {"size": 0.15, "decay": 0.45, "wet": 0.40},
        "Cathedral": {"size": 0.90, "decay": 0.85, "wet": 0.50},
    }

    # simuleaza acustica unei incaperi combinand piesa mea cu un zgomot matematic
    def process_reverb(self, preset="Room", intensity=1.0):
        if self.y_orig is None: return None
        y = self.y_orig.copy()

        # scot setarile pe care le-a ales userul
        p = self.REVERB_PRESETS.get(preset, self.REVERB_PRESETS["Room"])
        size = p["size"]
        decay = p["decay"]
        wet = min(p["wet"] * intensity, 0.95)

        # calculez cat de lung trebuie sa fie raspunsul incaperii
        ir_len = int(self.sr * size * 3)
        t = np.linspace(0, size * 3, ir_len)

        # generez "forma" fizica a camerei folosind zgomot alb (white noise)
        rng = np.random.default_rng(42)
        noise = rng.standard_normal(ir_len)
        # ii aplic un plic (envelope) ca sa scada in intensitate in timp, cum face ecoul in viata reala
        envelope = np.exp(-t / (decay + 1e-9))
        ir = noise * envelope
        ir /= np.max(np.abs(ir) + 1e-9)

        # functia minune care "loveste" fisierul meu de peretii virtuali proaspat calculati
        wet_signal = fftconvolve(y, ir, mode='full')[:len(y)]
        wet_signal /= (np.max(np.abs(wet_signal)) + 1e-9)

        # amestec sunetul original curat cu cel reverberat
        y_out = np.clip((1 - wet) * y + wet * wet_signal, -1.0, 1.0)
        self.y_proc = y_out
        return y_out

    # =========================================================
    # 3. STEREO ENHANCER (Effetune: 3D Audio)
    #    Mid/Side + Haas effect pe semnal mono
    # =========================================================
    # da impresia de spatialitate folosind o faza pacalita
    def process_stereo_enhancer(self, width=1.0, bass_mono_freq=120, side_gain=1.0):
        if self.y_orig is None: return None
        y = self.y_orig.copy()

        # intarzii semnalul putin cu vreo 15 milisecunde pentru efectul haas
        delay_samples = int(0.015 * self.sr)
        y_delayed = np.zeros_like(y)
        if delay_samples < len(y):
            y_delayed[delay_samples:] = y[:-delay_samples]

        # impart sunetul in centrul mixului (mid) si extreme (side)
        mid = (y + y_delayed) * 0.5
        side = (y - y_delayed) * 0.5 * side_gain * width

        # problema cu stereo fals e ca fura basul si il face varza, asa ca il monofiltrerz
        fft_side = np.fft.rfft(side)
        freqs = np.fft.rfftfreq(len(side), 1.0 / self.sr)
        # tot ce e sub pragul fixat de user (ex: 120hz) dispare de pe side si ramane doar pe centru
        fft_side[freqs < bass_mono_freq] = 0.0
        side_filtered = np.fft.irfft(fft_side, n=len(y))

        # combin la loc mid si side
        y_out = np.clip(mid + side_filtered, -1.0, 1.0)
        self.y_proc = y_out
        return y_out

    # =========================================================
    # 4. COMPRESOR CU ATAC/RELEASE (Effetune: Dynamics)
    #    Sample-accurate cu smoothing exponențial
    # =========================================================
    # compenseaza diferentele de volum ca sa nu mai am chestii care urla si altele care se aud prea incet
    def process_dynamics(self, threshold_db=-20, ratio=4, makeup_gain=6):
        if self.y_orig is None: return None
        y = self.y_orig.copy()

        # trec db in valori liniare cu care poate calcula procesorul direct
        threshold_lin = 10 ** (threshold_db / 20.0)
        makeup_lin = 10 ** (makeup_gain / 20.0)

        # timpii in care actioneaza compresorul. attack e fix pe 10ms, release pe 200ms
        attack_coeff = np.exp(-1.0 / (self.sr * 0.010))
        release_coeff = np.exp(-1.0 / (self.sr * 0.200))

        gain_smooth = 1.0
        output = np.zeros_like(y)
        # iau fisierul sample cu sample si il compar cu limitele de volum impuse
        for i, sample in enumerate(y):
            level = abs(sample)
            # daca trece de prag il "turtim" matematic dupa ratio stabilit
            if level > threshold_lin:
                target = threshold_lin * (level / threshold_lin) ** (1.0 / ratio) / (level + 1e-12)
            else:
                target = 1.0

            # calculez curbele line ca compresorul sa nu "muste" brusc ci sa revina frumos
            if target < gain_smooth:
                gain_smooth = attack_coeff * gain_smooth + (1 - attack_coeff) * target
            else:
                gain_smooth = release_coeff * gain_smooth + (1 - release_coeff) * target

            # salvez monstra procesata in care adaug si volumul de machiaj la final (makeup)
            output[i] = sample * gain_smooth * makeup_lin

        y_out = np.clip(output, -1.0, 1.0)
        self.y_proc = y_out
        return y_out

    # =========================================================
    # 5. NOISE GATE (Effetune: Gate)
    #    Threshold + Attack/Hold/Release
    # =========================================================
    # da mute automat la sunet atunci cand e prea incet, eliminand zgomotul microfonului pe pauze
    def process_noise_gate(self, threshold_db=-40, attack_ms=5, hold_ms=50, release_ms=100):
        if self.y_orig is None: return None
        y = self.y_orig.copy()

        threshold_lin = 10 ** (threshold_db / 20.0)
        attack_coeff = np.exp(-1.0 / (self.sr * max(attack_ms, 0.1) / 1000.0))
        release_coeff = np.exp(-1.0 / (self.sr * max(release_ms, 1.0) / 1000.0))
        hold_samples = int(hold_ms / 1000.0 * self.sr)

        gate_gain = 0.0
        hold_counter = 0
        output = np.zeros_like(y)

        # la fel ca la compresor, verific esantion cu esantion daca e destul de tare
        for i, sample in enumerate(y):
            # daca a depasit limita, deschidem poarta si resetam timerul de asteptare
            if abs(sample) >= threshold_lin:
                hold_counter = hold_samples
                target = 1.0
            # daca a coborat sub limita, lasam poarta deschisa inca o perioada de gratie (hold)
            elif hold_counter > 0:
                hold_counter -= 1
                target = 1.0
            # altfel cerem inchiderea treptata a portii (liniste)
            else:
                target = 0.0

            # netezesc trecerea dintre inchis deschis ca sa nu sune a taietura de foarfeca
            if target > gate_gain:
                gate_gain = attack_coeff * gate_gain + (1 - attack_coeff) * target
            else:
                gate_gain = release_coeff * gate_gain + (1 - release_coeff) * target
            output[i] = sample * gate_gain

        self.y_proc = output
        return output

    # =========================================================
    # 6. PITCH SHIFTER (Effetune)
    #    Semitone + Fine cents + Time Stretch
    # =========================================================
    # se ocupa de schimbarea grosimii vocii si de viteza piesei
    def process_pitch_tempo(self, pitch_semitones=0, fine_cents=0, tempo_rate=1.0):
        if self.y_orig is None: return None
        y = self.y_orig.copy()

        # calculez toti pasii inclusiv zecimalele din centi (1 sfert de ton, etc)
        total_steps = pitch_semitones + fine_cents / 100.0
        try:
            # las librosa sa faca munca grea cu faza vocodera ca e o matematica naspa aici
            if total_steps != 0:
                y = librosa.effects.pitch_shift(y, sr=self.sr, n_steps=total_steps)
            if tempo_rate != 1.0:
                y = librosa.effects.time_stretch(y, rate=tempo_rate)
        except Exception:
            pass
        y = np.clip(y, -1.0, 1.0)
        self.y_proc = y
        return y

    # =========================================================
    # 7. DELAY & ECHO (Menținut)
    # =========================================================
    # repeta sunetul in descrestere, gen ecoul strigatelor la munte
    def process_delay(self, delay_ms, feedback, mix):
        if self.y_orig is None: return None
        y = self.y_orig.copy()
        # convertesc milisecundele dorite in numar efectiv de cadre
        delay_samples = int((delay_ms / 1000.0) * self.sr)
        if delay_samples == 0:
            self.y_proc = y
            return y

        y_out = np.zeros_like(y)
        y_out += y
        current_delay = delay_samples
        current_gain = feedback

        # fac doar 5 repetitii ca sa nu supraincarc procesorul
        for _ in range(5):
            if current_delay >= len(y): break
            # shiftez la dreapta tot continutul, lasand zero in urma
            y_delayed = np.zeros_like(y)
            y_delayed[current_delay:] = y[:-current_delay]
            y_out += y_delayed * current_gain

            # scad incet volumul si maresc delay-ul in bucla ca sa dispara in fundal
            current_delay += delay_samples
            current_gain *= feedback

        # amestec delay-ul cu sunetul principal in procentele date si fortez limitele cu clip
        y_final = np.clip(y * (1 - mix) + y_out * mix, -1.0, 1.0)
        self.y_proc = y_final
        return y_final

    # =========================================================
    # 8. CHORUS (Menținut)
    # =========================================================
    # imita prezenta mai multor voci / chitare care canta in acelasi timp, usor dezacordate
    def process_chorus(self, depth_semitones, mix):
        if self.y_orig is None: return None
        y = self.y_orig.copy()
        try:
            # creez doua dubluri ale piesei si le decalez putin frecventa sus-jos
            y_up = librosa.effects.pitch_shift(y, sr=self.sr, n_steps=depth_semitones)
            y_down = librosa.effects.pitch_shift(y, sr=self.sr, n_steps=-depth_semitones)
            # le amestec toate trei
            y_out = y * (1 - mix) + (y_up * 0.5 + y_down * 0.5) * mix
        except Exception:
            y_out = y
        self.y_proc = np.clip(y_out, -1.0, 1.0)
        return self.y_proc

    # =========================================================
    # 9. WIENER FILTER (Menținut)
    # =========================================================
    # cel mai bun prieten pentru taiat zgomotul de laptop, aer conditionat, fasaiala
    def process_wiener(self, alpha):
        if self.y_orig is None: return None
        y = self.y_orig.copy()
        # apelez modulul noisereduce care foloseste un filtru wiener bazat pe statistica spectrala
        y_curat = nr.reduce_noise(y=y, sr=self.sr, prop_decrease=alpha / 1000.0, stationary=True)
        self.y_proc = y_curat
        return y_curat

    # =========================================================
    # UTILS – grafice si salvari
    # =========================================================

    # scrie fisierul wav temporar ca sa il poata lua gradioul
    def export_wav(self, y):
        temp_dir = tempfile.gettempdir()
        out_path = f"{temp_dir}/EQ_Master_Output.wav"
        sf.write(out_path, y, self.sr)
        return out_path

    # deseneaza unda vizuala obisnuita a piesei
    def plot_waveform(self, y, title, color="#3b82f6"):
        fig, ax = plt.subplots(figsize=(8, 2), dpi=100)
        fig.patch.set_facecolor('#141420')
        ax.set_facecolor('#0d0d12')

        # creez o axa de x bazata pe timp in secunde
        times = np.linspace(0, len(y) / self.sr, num=len(y))

        # daca piesa e prea lunga, sar monstre ca sa nu imi bubuie memoria cand randeaza poza
        if len(y) > 50000:
            step = len(y) // 50000
            times = times[::step]
            y_plot = y[::step]
        else:
            y_plot = y

        # pictez plot-ul in matplotlib cu culorile dark pe care le am in restul aplicatiei
        ax.plot(times, y_plot, color=color, alpha=0.8, linewidth=0.5)
        ax.set_title(title, color='white', fontsize=10)
        ax.set_xlabel("Timp (s)", color='#a0aec0', fontsize=8)
        ax.tick_params(colors='#a0aec0', labelsize=8)
        for spine in ax.spines.values(): spine.set_color('#2d2d44')
        plt.tight_layout()
        out_img = f"{tempfile.gettempdir()}/wave_temp.png"
        fig.savefig(out_img, facecolor=fig.get_facecolor())
        plt.close(fig)
        return out_img

    # deseneaza spectrograma tip "foc", unde putem vedea ce frecvente au energie mai multa
    def plot_spectrogram(self, y, title):
        fig, ax = plt.subplots(figsize=(6, 3.5), dpi=100)
        fig.patch.set_facecolor('#141420')

        # calculez decibelii din stft si fac heatmapul
        D = librosa.amplitude_to_db(np.abs(librosa.stft(y)) + 1e-10, ref=np.max)
        img = librosa.display.specshow(D, sr=self.sr, x_axis='time', y_axis='log', cmap='magma', ax=ax)

        ax.set_title(title, color='white', fontsize=10)
        ax.set_xlabel("Timp", color='#a0aec0')
        ax.set_ylabel("Frecvență (Hz)", color='#a0aec0')
        ax.tick_params(colors='#a0aec0')
        plt.tight_layout()
        out_img = f"{tempfile.gettempdir()}/spec_temp.png"
        fig.savefig(out_img, facecolor=fig.get_facecolor())
        plt.close(fig)
        return out_img

    # simuleaza acel panou de control pe care il vezi la doctorul orl
    # arata fix cat volum in decibeli genereaza anumite frecvente fixate
    def plot_audiogram(self, data):
        # sparg informatia doar in real math fft ca sa o scot curata fara faze
        fourier_transform_magnitude = np.abs(rfft(data))
        fourier_transform_dB = 20 * np.log10(fourier_transform_magnitude + 1e-10)
        fourier_transform_freq = np.real(rfftfreq(len(data), 1 / self.sr))

        # definesc limitele vizuale ale testului auditiv
        audiogram_frequencies = [0, 50, 100, 200, 400, 800, 1600, 2000, 4000, 8000, 16000, 20000]
        audiogram_dB = []

        # asociez frecventele cele mai apropiate de pe hartie cu rezultatele
        for freq in audiogram_frequencies:
            idx = np.argmin(np.abs(fourier_transform_freq - freq))
            audiogram_dB.append(fourier_transform_dB[idx])

        # un truc vizual prin care indoi graficul ca sa inghesui o plaja atat de mare vizual frumos
        def custom_transform(x):
            return np.where(x <= 2000, x, 2000 + (x - 2000) * (2000 / 18000))

        transformed_frequencies = custom_transform(np.array(audiogram_frequencies))
        fig, ax = plt.subplots(figsize=(6, 3.5), dpi=100)
        fig.patch.set_facecolor('#141420')
        ax.set_facecolor('#0d0d12')
        ax.plot(transformed_frequencies, audiogram_dB, 'x-', label="Nivel Semnal", color='#00ffff')

        original_ticks = [0, 1000, 2000, 10000, 20000]
        transformed_ticks = custom_transform(np.array(original_ticks))
        ax.set_xticks(transformed_ticks)
        ax.set_xticklabels([str(t) for t in original_ticks])

        # graficul doctorului are axa y inversata, cele mai tari sunete sunt jos
        ax.invert_yaxis()
        ax.set_xlabel("Frecvență (Hz)", color='#a0aec0')
        ax.set_ylabel("Intensitate (dB HL)", color='#a0aec0')
        ax.tick_params(colors='#a0aec0')
        for spine in ax.spines.values(): spine.set_color('#2d2d44')
        plt.tight_layout()
        out_img = f"{tempfile.gettempdir()}/audiogram_temp.png"
        fig.savefig(out_img, facecolor=fig.get_facecolor())
        plt.close(fig)
        return out_img