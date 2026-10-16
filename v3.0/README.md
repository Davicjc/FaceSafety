# 🛡️ Face Safety v3.0 (Versão Moderna)

Esta é a **nova geração do Face Safety**, reconstruída com métodos modernos de Visão Computacional para manter o legado do projeto vivo e funcionando perfeitamente nos sistemas atuais, sem a complexidade de instalação da versão antiga.

---

## 📂 Arquivos desta pasta

- **[`FaceSafety-v3.0.exe`](FaceSafety-v3.0.exe)** — Executável standalone para **Windows** (1 Clique: basta baixar e abrir, sem precisar instalar Python nem abrir o terminal!).
- **[`facesafety.py`](facesafety.py)** — Código-fonte completo e unificado (compatível com **Windows, Linux, macOS e Raspberry Pi**).
- **[`requirements.txt`](requirements.txt)** — Lista mínima de dependências (`opencv-python` e `numpy`).

---

## 🚀 Opção 1: Executar com 1 Clique (Windows `.exe`)

1. Baixe o arquivo **[`FaceSafety-v3.0.exe`](FaceSafety-v3.0.exe)**.
2. Dê dois cliques nele para abrir.
3. Na primeira execução, ele criará automaticamente uma pasta `dados/` ao lado do executável e baixará os modelos neurais leves do OpenCV (**YuNet** e **SFace**).

> 💡 **Nota:** Caso queira editar a função `key()` para integrar com Arduino, Raspberry Pi ou automação, utilize a **Opção 2** (via código-fonte `.py`).

---

## 💻 Opção 2: Rodar pelo Código-Fonte (Windows, Linux, macOS, Raspberry Pi)

Com o **Python 3.9+** instalado, abra o terminal nesta pasta (`v3.0`) e execute:

```bash
pip install -r requirements.txt
python facesafety.py
```

Não é necessário instalar `dlib`, `face_recognition`, `CMake` nem `Visual Studio C++`!
