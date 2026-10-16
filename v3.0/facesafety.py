# ------------------------------------------------------------------------------------------------------------
# FACE SAFETY 3.0 — Reconhecimento Facial e Controle de Acesso
# Criado originalmente por Davi Castro (Davicjc) — https://github.com/Davicjc | https://davicjc.com
#
# Versão moderna, unificada (Windows, Linux e macOS) e sem dependências pesadas (sem dlib / CMake / Visual Studio).
# Utiliza o motor neural nativo do OpenCV (YuNet + SFace ONNX), baixando os modelos automaticamente na 1ª execução.
#
# Instalação única (via código-fonte):
#   pip install opencv-python
#
# Para personalizar a ação de liberação de acesso (trancas, relés, Raspberry Pi, Arduino, APIs),
# edite a função `key(nome)` no final deste arquivo!
# ------------------------------------------------------------------------------------------------------------

import os
import sys
import time
import threading
import urllib.request
import webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import cv2
import numpy as np


# ============================================================================================================
# CONFIGURAÇÕES E DIRETÓRIOS (Compatível com script .py e executável .exe PyInstaller)
# ============================================================================================================

if getattr(sys, "frozen", False):
    # Quando executado via .exe, salva a pasta `dados` ao lado do executável
    BASE_DIR = Path(sys.executable).resolve().parent
    BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", BASE_DIR))
else:
    BASE_DIR = Path(__file__).resolve().parent
    BUNDLE_DIR = BASE_DIR

DATA_DIR = BASE_DIR / "dados"
FACES_DIR = DATA_DIR / "rostos"
MODELS_DIR = DATA_DIR / "models"
ADMS_FILE = DATA_DIR / "adms.txt"

YUNET_FILENAME = "face_detection_yunet_2023mar.onnx"
SFACE_FILENAME = "face_recognition_sface_2021dec.onnx"

YUNET_URL = (
    "https://github.com/opencv/opencv_zoo/raw/main/models/"
    f"face_detection_yunet/{YUNET_FILENAME}"
)
SFACE_URL = (
    "https://github.com/opencv/opencv_zoo/raw/main/models/"
    f"face_recognition_sface/{SFACE_FILENAME}"
)

# Limiar de similaridade de cosseno do SFace (padrão recomendado pelo OpenCV Zoo: 0.363)
COSINE_THRESHOLD = 0.38


# ============================================================================================================
# MOTOR DE RECONHECIMENTO FACIAL (OpenCV YuNet + SFace)
# ============================================================================================================

class FaceEngine:
    """Gerencia detecção, extração de características (128D) e banco de rostos local."""

    def __init__(self):
        self.detector = None
        self.recognizer = None
        self.known_embeddings = {}  # {nome: np.ndarray (1, 128)}
        self.admins = set()
        self._ensure_dirs()
        self._load_admins()

    def _ensure_dirs(self):
        FACES_DIR.mkdir(parents=True, exist_ok=True)
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        if not ADMS_FILE.exists():
            ADMS_FILE.write_text("", encoding="utf-8")

    def _get_model_paths(self) -> tuple[Path, Path]:
        """Verifica se os modelos estão embutidos no .exe ou na pasta dados/models."""
        bundled_yunet = BUNDLE_DIR / "models" / YUNET_FILENAME
        bundled_sface = BUNDLE_DIR / "models" / SFACE_FILENAME
        yunet = bundled_yunet if bundled_yunet.exists() else (MODELS_DIR / YUNET_FILENAME)
        sface = bundled_sface if bundled_sface.exists() else (MODELS_DIR / SFACE_FILENAME)
        return yunet, sface

    def models_ready(self) -> bool:
        yunet, sface = self._get_model_paths()
        return (
            yunet.exists()
            and yunet.stat().st_size > 100_000
            and sface.exists()
            and sface.stat().st_size > 10_000_000
        )

    def download_models(self, progress_callback=None):
        """Baixa os modelos ONNX oficiais do OpenCV Zoo caso ainda não existam."""
        yunet, sface = self._get_model_paths()
        models = [
            ("Detector Facial (YuNet)", YUNET_URL, yunet),
            ("Reconhecedor Facial (SFace)", SFACE_URL, sface),
        ]
        for label, url, dest in models:
            if dest.exists() and dest.stat().st_size > 100_000:
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = dest.with_suffix(".tmp")

            def _hook(block_num, block_size, total_size, lbl=label):
                if progress_callback and total_size > 0:
                    pct = min(100, int(block_num * block_size * 100 / total_size))
                    progress_callback(f"Baixando {lbl}... {pct}%")

            if progress_callback:
                progress_callback(f"Baixando {label}...")
            urllib.request.urlretrieve(url, tmp_path, reporthook=_hook)
            tmp_path.replace(dest)

    def init_models(self, progress_callback=None):
        """Inicializa os modelos YuNet e SFace e carrega os rostos cadastrados."""
        if not self.models_ready():
            self.download_models(progress_callback)

        yunet, sface = self._get_model_paths()
        if self.detector is None:
            self.detector = cv2.FaceDetectorYN.create(
                str(yunet), "", (320, 320), 0.75, 0.3, 5000
            )
        if self.recognizer is None:
            self.recognizer = cv2.FaceRecognizerSF.create(str(sface), "")

        self.reload_database()

    # -------------------- Banco de Dados de Pessoas e ADMs --------------------

    def _load_admins(self):
        if ADMS_FILE.exists():
            lines = ADMS_FILE.read_text(encoding="utf-8").splitlines()
            self.admins = {line.strip() for line in lines if line.strip()}
        else:
            self.admins = set()

    def _save_admins(self):
        ADMS_FILE.write_text("\n".join(sorted(self.admins)), encoding="utf-8")

    def is_admin(self, name: str) -> bool:
        return name in self.admins

    def set_admin(self, name: str, enabled: bool):
        if enabled:
            self.admins.add(name)
        else:
            self.admins.discard(name)
        self._save_admins()

    def toggle_admin(self, name: str) -> bool:
        new_state = name not in self.admins
        self.set_admin(name, new_state)
        return new_state

    @staticmethod
    def _imread_unicode(path: Path):
        """Lê imagens mesmo em caminhos com acentos no Windows."""
        data = np.fromfile(str(path), dtype=np.uint8)
        if data.size == 0:
            return None
        return cv2.imdecode(data, cv2.IMREAD_COLOR)

    @staticmethod
    def _imwrite_unicode(path: Path, img) -> bool:
        """Salva imagens mesmo em caminhos com acentos no Windows."""
        ok, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
        if ok:
            buf.tofile(str(path))
        return ok

    def extract_biggest_face(self, bgr_img):
        """Retorna (face_box_landmark, embedding_128d) do maior rosto na imagem, ou (None, None)."""
        if bgr_img is None or self.detector is None or self.recognizer is None:
            return None, None
        h, w = bgr_img.shape[:2]
        scale = 640.0 / w if w > 640 else 1.0
        small = cv2.resize(bgr_img, (int(w * scale), int(h * scale))) if scale != 1.0 else bgr_img
        sh, sw = small.shape[:2]
        self.detector.setInputSize((sw, sh))
        _, faces = self.detector.detect(small)
        if faces is None or len(faces) == 0:
            return None, None
        # Seleciona o maior rosto pela área (w * h)
        biggest = max(faces, key=lambda f: f[2] * f[3]).copy()
        if scale != 1.0:
            biggest[:14] = biggest[:14] / scale
        aligned = self.recognizer.alignCrop(bgr_img, biggest)
        feat = self.recognizer.feature(aligned)
        return biggest, feat

    def reload_database(self):
        """Carrega todas as pessoas da pasta `dados/rostos`."""
        self._load_admins()
        self.known_embeddings.clear()

        for img_path in sorted(FACES_DIR.glob("*.jpg")):
            name = img_path.stem
            npy_path = img_path.with_suffix(".npy")

            if npy_path.exists():
                try:
                    feat = np.load(str(npy_path))
                    self.known_embeddings[name] = feat
                    continue
                except Exception:
                    pass

            if self.detector is not None and self.recognizer is not None:
                img = self._imread_unicode(img_path)
                _, feat = self.extract_biggest_face(img)
                if feat is not None:
                    np.save(str(npy_path), feat)
                    self.known_embeddings[name] = feat

    def register_person(self, name: str, bgr_img, make_admin: bool = False) -> tuple[bool, str]:
        """Valida o rosto na imagem, salva foto + vetor 128D e atualiza o banco."""
        clean_name = "".join(c for c in name.strip() if c not in r'\/:*?"<>|')
        if not clean_name:
            return False, "Digite um nome válido para cadastrar."

        face, feat = self.extract_biggest_face(bgr_img)
        if face is None or feat is None:
            return False, "Nenhum rosto nítido foi detectado na imagem. Olhe para a câmera com boa iluminação!"

        img_path = FACES_DIR / f"{clean_name}.jpg"
        npy_path = FACES_DIR / f"{clean_name}.npy"

        self._imwrite_unicode(img_path, bgr_img)
        np.save(str(npy_path), feat)
        self.known_embeddings[clean_name] = feat

        if make_admin:
            self.set_admin(clean_name, True)

        return True, f"'{clean_name}' cadastrado(a) com sucesso!"

    def remove_person(self, name: str) -> bool:
        removed = False
        for ext in (".jpg", ".npy"):
            p = FACES_DIR / f"{name}{ext}"
            if p.exists():
                p.unlink()
                removed = True
        self.known_embeddings.pop(name, None)
        self.set_admin(name, False)
        return removed

    def detect_and_recognize(self, bgr_frame):
        """
        Detecta todos os rostos no quadro e compara com o banco de dados.
        Retorna lista de dicts: [{'box': (x, y, w, h), 'name': str, 'score': float, 'is_admin': bool, 'known': bool}]
        """
        if self.detector is None or self.recognizer is None:
            return []

        h, w = bgr_frame.shape[:2]
        scale = 1.0
        if w > 640:
            scale = 640.0 / w
            small = cv2.resize(bgr_frame, (int(w * scale), int(h * scale)))
        else:
            small = bgr_frame

        sh, sw = small.shape[:2]
        self.detector.setInputSize((sw, sh))
        _, faces = self.detector.detect(small)

        results = []
        if faces is None:
            return results

        for face in faces:
            face_orig = face.copy()
            if scale != 1.0:
                face_orig[:14] = face_orig[:14] / scale

            aligned = self.recognizer.alignCrop(bgr_frame, face_orig)
            feat = self.recognizer.feature(aligned)

            best_name = "Nao Cadastrado"
            best_score = 0.0
            known = False

            for person_name, known_feat in self.known_embeddings.items():
                score = float(
                    self.recognizer.match(feat, known_feat, cv2.FaceRecognizerSF_FR_COSINE)
                )
                if score > best_score:
                    best_score = score
                    if score >= COSINE_THRESHOLD:
                        best_name = person_name
                        known = True

            x, y, fw, fh = (
                int(face_orig[0]),
                int(face_orig[1]),
                int(face_orig[2]),
                int(face_orig[3]),
            )
            results.append(
                {
                    "box": (x, y, fw, fh),
                    "name": best_name,
                    "score": best_score,
                    "known": known,
                    "is_admin": known and self.is_admin(best_name),
                }
            )

        return results


# ============================================================================================================
# INTERFACE GRÁFICA MODERNA (Tkinter Dark UI c/ Câmera Embutida)
# ============================================================================================================

class FaceSafetyApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("FACE SAFETY 3.0 — Controle de Acesso Facial")
        self.root.geometry("980x620")
        self.root.minsize(900, 560)
        self.root.configure(bg="#0f172a")

        self.engine = FaceEngine()
        self.cap = None
        self.running = False
        self.current_frame = None
        self._photo_ref = None
        self._key_lock = threading.Lock()
        self._last_key_time = 0.0

        self._build_ui()
        self._init_engine_async()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        # Cabeçalho
        header = tk.Frame(self.root, bg="#0b1120", height=56)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        title_lbl = tk.Label(
            header,
            text="🛡️ FACE SAFETY 3.0",
            font=("Segoe UI", 16, "bold"),
            bg="#0b1120",
            fg="#f8fafc",
        )
        title_lbl.pack(side="left", padx=20)

        subtitle_lbl = tk.Label(
            header,
            text="Reconhecimento Facial & Controle de Acesso",
            font=("Segoe UI", 10),
            bg="#0b1120",
            fg="#94a3b8",
        )
        subtitle_lbl.pack(side="left", padx=4)

        credit_lbl = tk.Label(
            header,
            text="By: Davicjc ↗",
            font=("Segoe UI", 10, "underline"),
            bg="#0b1120",
            fg="#38bdf8",
            cursor="hand2",
        )
        credit_lbl.pack(side="right", padx=20)
        credit_lbl.bind("<Button-1>", lambda _: webbrowser.open("https://github.com/Davicjc/"))

        # Corpo principal
        body = tk.Frame(self.root, bg="#0f172a")
        body.pack(fill="both", expand=True, padx=16, pady=12)

        # Coluna Esquerda: Vídeo / Scanner
        left_col = tk.Frame(body, bg="#1e293b", bd=0, highlightthickness=1, highlightbackground="#334155")
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 12))

        cam_bar = tk.Frame(left_col, bg="#1e293b")
        cam_bar.pack(fill="x", padx=12, pady=10)

        self.btn_scanner = tk.Button(
            cam_bar,
            text="▶ Ligar Câmera / Scanner",
            font=("Segoe UI", 10, "bold"),
            bg="#10b981",
            fg="#ffffff",
            activebackground="#059669",
            activeforeground="#ffffff",
            relief="flat",
            padx=14,
            pady=6,
            cursor="hand2",
            command=self.toggle_scanner,
        )
        self.btn_scanner.pack(side="left")

        tk.Label(
            cam_bar, text="Câmera:", font=("Segoe UI", 9), bg="#1e293b", fg="#cbd5e1"
        ).pack(side="left", padx=(14, 4))

        self.cam_idx_var = tk.StringVar(value="0")
        cam_spin = ttk.Spinbox(cam_bar, from_=0, to=4, width=3, textvariable=self.cam_idx_var, state="readonly")
        cam_spin.pack(side="left")

        self.fps_label = tk.Label(
            cam_bar,
            text="Scanner desligado",
            font=("Segoe UI", 9),
            bg="#1e293b",
            fg="#94a3b8",
        )
        self.fps_label.pack(side="right")

        # Área de vídeo
        self.video_label = tk.Label(
            left_col,
            text="Câmera desligada\n\nClique em '▶ Ligar Câmera / Scanner' acima\npara iniciar o monitoramento ou capturar fotos.",
            font=("Segoe UI", 12),
            bg="#090d16",
            fg="#64748b",
            justify="center",
        )
        self.video_label.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        # Coluna Direita: Cadastros e ADMs
        right_col = tk.Frame(body, bg="#1e293b", width=330, highlightthickness=1, highlightbackground="#334155")
        right_col.pack(side="right", fill="y")
        right_col.pack_propagate(False)

        # Card: Cadastrar Nova Pessoa
        reg_frame = tk.Frame(right_col, bg="#1e293b")
        reg_frame.pack(fill="x", padx=14, pady=(12, 8))

        tk.Label(
            reg_frame,
            text="➕ Cadastrar Pessoa",
            font=("Segoe UI", 11, "bold"),
            bg="#1e293b",
            fg="#f8fafc",
        ).pack(anchor="w")

        tk.Label(
            reg_frame,
            text="Nome da pessoa:",
            font=("Segoe UI", 9),
            bg="#1e293b",
            fg="#cbd5e1",
        ).pack(anchor="w", pady=(6, 2))

        self.entry_name = tk.Entry(
            reg_frame,
            font=("Segoe UI", 10),
            bg="#0f172a",
            fg="#f8fafc",
            insertbackground="#f8fafc",
            relief="flat",
            highlightthickness=1,
            highlightbackground="#475569",
            highlightcolor="#38bdf8",
        )
        self.entry_name.pack(fill="x", ipady=5)

        self.var_make_adm = tk.BooleanVar(value=False)
        chk_adm = tk.Checkbutton(
            reg_frame,
            text="Cadastrar como Administrador (aciona função KEY)",
            variable=self.var_make_adm,
            font=("Segoe UI", 9),
            bg="#1e293b",
            fg="#fbbf24",
            selectcolor="#0f172a",
            activebackground="#1e293b",
            activeforeground="#fbbf24",
        )
        chk_adm.pack(anchor="w", pady=(6, 6))

        btn_row = tk.Frame(reg_frame, bg="#1e293b")
        btn_row.pack(fill="x")

        btn_capture = tk.Button(
            btn_row,
            text="📸 Capturar da Câmera",
            font=("Segoe UI", 9, "bold"),
            bg="#3b82f6",
            fg="#ffffff",
            activebackground="#2563eb",
            activeforeground="#ffffff",
            relief="flat",
            pady=6,
            cursor="hand2",
            command=self.capture_from_camera,
        )
        btn_capture.pack(side="left", fill="x", expand=True, padx=(0, 4))

        btn_import = tk.Button(
            btn_row,
            text="📁 Foto...",
            font=("Segoe UI", 9),
            bg="#334155",
            fg="#f8fafc",
            activebackground="#475569",
            activeforeground="#ffffff",
            relief="flat",
            padx=10,
            pady=6,
            cursor="hand2",
            command=self.import_from_file,
        )
        btn_import.pack(side="right")

        ttk.Separator(right_col, orient="horizontal").pack(fill="x", padx=14, pady=8)

        # Card: Lista de Pessoas e ADMs
        list_frame = tk.Frame(right_col, bg="#1e293b")
        list_frame.pack(fill="both", expand=True, padx=14, pady=(0, 12))

        self.lbl_count = tk.Label(
            list_frame,
            text="👥 Pessoas Cadastradas (0)",
            font=("Segoe UI", 11, "bold"),
            bg="#1e293b",
            fg="#f8fafc",
        )
        self.lbl_count.pack(anchor="w", pady=(0, 6))

        list_container = tk.Frame(list_frame, bg="#0f172a", highlightthickness=1, highlightbackground="#334155")
        list_container.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(list_container, orient="vertical")
        scrollbar.pack(side="right", fill="y")

        self.people_listbox = tk.Listbox(
            list_container,
            font=("Consolas", 10),
            bg="#0f172a",
            fg="#e2e8f0",
            selectbackground="#2563eb",
            selectforeground="#ffffff",
            relief="flat",
            bd=0,
            highlightthickness=0,
            activestyle="none",
            yscrollcommand=scrollbar.set,
        )
        self.people_listbox.pack(side="left", fill="both", expand=True, padx=4, pady=4)
        scrollbar.config(command=self.people_listbox.yview)

        actions_row = tk.Frame(list_frame, bg="#1e293b")
        actions_row.pack(fill="x", pady=(8, 0))

        btn_toggle_adm = tk.Button(
            actions_row,
            text="⭐ + / - ADM",
            font=("Segoe UI", 9, "bold"),
            bg="#d97706",
            fg="#ffffff",
            activebackground="#b45309",
            activeforeground="#ffffff",
            relief="flat",
            pady=6,
            cursor="hand2",
            command=self.toggle_selected_admin,
        )
        btn_toggle_adm.pack(side="left", fill="x", expand=True, padx=(0, 4))

        btn_delete = tk.Button(
            actions_row,
            text="🗑️ Remover",
            font=("Segoe UI", 9, "bold"),
            bg="#ef4444",
            fg="#ffffff",
            activebackground="#dc2626",
            activeforeground="#ffffff",
            relief="flat",
            pady=6,
            cursor="hand2",
            command=self.delete_selected_person,
        )
        btn_delete.pack(side="right", fill="x", expand=True, padx=(4, 0))

        # Barra de Status inferior
        status_bar = tk.Frame(self.root, bg="#0b1120", height=32)
        status_bar.pack(fill="x", side="bottom")
        status_bar.pack_propagate(False)

        self.status_var = tk.StringVar(value="Inicializando modelos de inteligência artificial...")
        status_lbl = tk.Label(
            status_bar,
            textvariable=self.status_var,
            font=("Segoe UI", 9),
            bg="#0b1120",
            fg="#38bdf8",
        )
        status_lbl.pack(side="left", padx=16)

        folder_btn = tk.Label(
            status_bar,
            text="📂 Abrir pasta de dados",
            font=("Segoe UI", 9, "underline"),
            bg="#0b1120",
            fg="#94a3b8",
            cursor="hand2",
        )
        folder_btn.pack(side="right", padx=16)
        folder_btn.bind("<Button-1>", lambda _: self._open_data_folder())

    # -------------------- Inicialização Assíncrona dos Modelos --------------------

    def _init_engine_async(self):
        def _worker():
            try:
                self.engine.init_models(
                    progress_callback=lambda msg: self.root.after(0, self.status_var.set, msg)
                )
                self.root.after(0, self._on_engine_ready)
            except Exception as exc:
                self.root.after(
                    0,
                    self.status_var.set,
                    f"Erro ao inicializar modelos: {exc}",
                )

        threading.Thread(target=_worker, daemon=True).start()

    def _on_engine_ready(self):
        self.refresh_people_list()
        self.status_var.set(
            f"Pronto! {len(self.engine.known_embeddings)} pessoa(s) carregada(s). Pasta: {FACES_DIR}"
        )

    # -------------------- Gerenciamento de Pessoas e ADMs --------------------

    def refresh_people_list(self):
        self.people_listbox.delete(0, "end")
        names = sorted(self.engine.known_embeddings.keys(), key=str.lower)
        for name in names:
            badge = "⭐ [ADM] " if self.engine.is_admin(name) else "👤       "
            self.people_listbox.insert("end", f"{badge}{name}")
        self.lbl_count.config(text=f"👥 Pessoas Cadastradas ({len(names)})")

    def _get_selected_name(self):
        sel = self.people_listbox.curselection()
        if not sel:
            messagebox.showwarning("Atenção", "Selecione uma pessoa na lista primeiro!")
            return None
        names = sorted(self.engine.known_embeddings.keys(), key=str.lower)
        idx = sel[0]
        return names[idx] if 0 <= idx < len(names) else None

    def capture_from_camera(self):
        name = self.entry_name.get().strip()
        if not name:
            messagebox.showwarning("Nome obrigatório", "Digite o nome da pessoa antes de capturar!")
            self.entry_name.focus_set()
            return

        frame_to_use = None
        if self.running and self.current_frame is not None:
            frame_to_use = self.current_frame.copy()
        else:
            self.status_var.set("Abrindo câmera para captura...")
            self.root.update_idletasks()
            cap = self._open_camera()
            if cap is not None and cap.isOpened():
                ret, frm = False, None
                for _ in range(8):
                    ret, frm = cap.read()
                if ret and frm is not None:
                    frame_to_use = frm
                cap.release()

        if frame_to_use is None:
            messagebox.showerror(
                "Erro na Câmera",
                "Não foi possível capturar imagem da câmera. Verifique se ela está conectada ou ligue o Scanner primeiro.",
            )
            return

        ok, msg = self.engine.register_person(name, frame_to_use, make_admin=self.var_make_adm.get())
        if ok:
            self.entry_name.delete(0, "end")
            self.var_make_adm.set(False)
            self.refresh_people_list()
            self.status_var.set(msg)
        else:
            messagebox.showwarning("Rosto não detectado", msg)

    def import_from_file(self):
        name = self.entry_name.get().strip()
        file_path = filedialog.askopenfilename(
            title="Selecione uma foto com o rosto da pessoa",
            filetypes=[("Imagens", "*.jpg *.jpeg *.png *.bmp *.webp")],
        )
        if not file_path:
            return
        if not name:
            name = Path(file_path).stem

        img = self.engine._imread_unicode(Path(file_path))
        ok, msg = self.engine.register_person(name, img, make_admin=self.var_make_adm.get())
        if ok:
            self.entry_name.delete(0, "end")
            self.var_make_adm.set(False)
            self.refresh_people_list()
            self.status_var.set(msg)
        else:
            messagebox.showwarning("Rosto não detectado", msg)

    def toggle_selected_admin(self):
        name = self._get_selected_name()
        if not name:
            return
        now_admin = self.engine.toggle_admin(name)
        self.refresh_people_list()
        estado = "adicionado aos ADMs ⭐" if now_admin else "removido dos ADMs"
        self.status_var.set(f"'{name}' foi {estado}.")

    def delete_selected_person(self):
        name = self._get_selected_name()
        if not name:
            return
        if messagebox.askyesno("Confirmar Exclusão", f"Deseja realmente remover '{name}' do banco de dados?"):
            self.engine.remove_person(name)
            self.refresh_people_list()
            self.status_var.set(f"Cadastro '{name}' removido.")

    # -------------------- Loop de Câmera e Scanner --------------------

    def _open_camera(self):
        idx = int(self.cam_idx_var.get() or 0)
        if sys.platform.startswith("win"):
            cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
            if not cap.isOpened():
                cap = cv2.VideoCapture(idx)
        else:
            cap = cv2.VideoCapture(idx)
        return cap

    def toggle_scanner(self):
        if self.running:
            self.stop_scanner()
        else:
            self.start_scanner()

    def start_scanner(self):
        if self.engine.detector is None:
            messagebox.showinfo("Aguarde", "Os modelos de IA ainda estão sendo carregados. Aguarde alguns segundos.")
            return

        self.cap = self._open_camera()
        if self.cap is None or not self.cap.isOpened():
            messagebox.showerror(
                "Câmera não encontrada",
                f"Não foi possível abrir a Câmera {self.cam_idx_var.get()}.\nVerifique se ela está conectada e não está sendo usada por outro app.",
            )
            return

        self.running = True
        self.btn_scanner.config(text="⏹ Parar Scanner", bg="#ef4444", activebackground="#dc2626")
        self.status_var.set("Scanner ativo — monitorando rostos em tempo real.")
        self._update_video_frame()

    def stop_scanner(self):
        self.running = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.btn_scanner.config(text="▶ Ligar Câmera / Scanner", bg="#10b981", activebackground="#059669")
        self.fps_label.config(text="Scanner desligado")
        self.video_label.config(
            image="",
            text="Câmera desligada\n\nClique em '▶ Ligar Câmera / Scanner' acima\npara iniciar o monitoramento ou capturar fotos.",
        )
        self._photo_ref = None
        self.status_var.set("Scanner parado.")

    def _update_video_frame(self):
        if not self.running or self.cap is None:
            return

        t0 = time.perf_counter()
        ret, frame = self.cap.read()
        if not ret or frame is None:
            self.stop_scanner()
            return

        self.current_frame = frame.copy()
        detections = self.engine.detect_and_recognize(frame)

        for det in detections:
            x, y, w, h = det["box"]
            name = det["name"]
            score = det["score"]
            is_admin = det["is_admin"]
            known = det["known"]

            if is_admin:
                color = (0, 191, 255)  # Dourado / Âmbar em BGR
                label = f"{name} [ADM] ({int(score * 100)}%)"
                self._trigger_key_async(name)
            elif known:
                color = (16, 185, 129)  # Verde em BGR
                label = f"{name} ({int(score * 100)}%)"
            else:
                color = (68, 68, 239)  # Vermelho em BGR
                label = "Nao Cadastrado"

            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_DUPLEX, 0.65, 1)
            ty = max(y - 8, th + 10)
            cv2.rectangle(frame, (x, ty - th - 8), (x + tw + 10, ty + 4), color, -1)
            cv2.putText(
                frame,
                label,
                (x + 5, ty - 2),
                cv2.FONT_HERSHEY_DUPLEX,
                0.65,
                (15, 23, 42) if is_admin else (255, 255, 255),
                1,
                cv2.LINE_AA,
            )

        lbl_w = max(self.video_label.winfo_width(), 480)
        lbl_h = max(self.video_label.winfo_height(), 360)
        fh, fw = frame.shape[:2]
        scale = min(lbl_w / fw, lbl_h / fh)
        disp = cv2.resize(frame, (max(1, int(fw * scale)), max(1, int(fh * scale))))

        ok, ppm_buf = cv2.imencode(".ppm", disp)
        if ok:
            photo = tk.PhotoImage(data=ppm_buf.tobytes())
            self._photo_ref = photo
            self.video_label.config(image=photo, text="")

        dt = max(1e-3, time.perf_counter() - t0)
        self.fps_label.config(text=f"{int(1.0 / dt)} FPS | {len(detections)} rosto(s)")

        if self.running:
            self.root.after(15, self._update_video_frame)

    def _trigger_key_async(self, admin_name: str):
        """Dispara a função `key(nome)` em segundo plano sem travar a câmera."""
        now = time.time()
        if now - self._last_key_time < 5.0 or self._key_lock.locked():
            return

        def _run():
            with self._key_lock:
                self._last_key_time = time.time()
                self.root.after(
                    0,
                    self.status_var.set,
                    f"🔑 ADM reconhecido ({admin_name})! Executando função key()...",
                )
                try:
                    key(admin_name)
                except Exception as exc:
                    print(f"[ERRO em key()]: {exc}")
                self._last_key_time = time.time()
                self.root.after(
                    0,
                    self.status_var.set,
                    f"🔒 Ciclo da função key() finalizado para '{admin_name}'.",
                )

        threading.Thread(target=_run, daemon=True).start()

    def _open_data_folder(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if sys.platform.startswith("win"):
            os.startfile(str(DATA_DIR))
        elif sys.platform == "darwin":
            os.system(f'open "{DATA_DIR}"')
        else:
            os.system(f'xdg-open "{DATA_DIR}"')

    def _on_close(self):
        self.running = False
        if self.cap is not None:
            self.cap.release()
        self.root.destroy()


# ============================================================================================================
# 🗝️ FUNÇÃO KEY — PERSONALIZE COMO QUISER!
# ============================================================================================================

def key(nome: str = ""):
    """
    Esta função é chamada automaticamente sempre que um Administrador (ADM) é reconhecido pela câmera.
    Ela roda em segundo plano (thread separada), portanto o `time.sleep(5)` NÃO trava o vídeo da câmera!

    Exemplos do que você pode colocar aqui:
      - Acionar um pino GPIO no Raspberry Pi para abrir uma fechadura solenoide / relé
      - Enviar comando via porta Serial (pyserial) para um Arduino / ESP32
      - Fazer uma requisição HTTP / Webhook para um sistema de automação residencial
    """
    print(f"[KEY] Acesso permitido para ADM '{nome}' por 5 segundos...")

    # --------------------------------------------------------------------------------------------------------
    # 1) COLOQUE ABAIXO SEU CÓDIGO PARA LIBERAR O ACESSO (ex: destrancar porta / ligar relé)
    # --------------------------------------------------------------------------------------------------------
    pass

    # Tempo em que o acesso permanece liberado (em segundos)
    time.sleep(5)

    print(f"[KEY] Acesso expirado após 5 segundos para '{nome}'.")

    # --------------------------------------------------------------------------------------------------------
    # 2) COLOQUE ABAIXO SEU CÓDIGO PARA ENCERRAR O ACESSO (ex: trancar porta / desligar relé)
    # --------------------------------------------------------------------------------------------------------
    pass


if __name__ == "__main__":
    root = tk.Tk()
    app = FaceSafetyApp(root)
    root.mainloop()
