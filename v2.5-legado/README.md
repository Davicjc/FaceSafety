# 🏛️ Face Safety v2.5 (Versão Clássica / Legado)

> **Nota Histórica:** Esta versão foi desenvolvida originalmente durante a época da faculdade, **100% feita à mão, linha por linha, antes da era das IAs generativas**, através de muita pesquisa em documentações, testes de bibliotecas e estudos práticos em Python.

Ela foi mantida intacta nesta pasta como registro histórico da evolução do projeto. Para uso atual em sistemas modernos, **recomendamos fortemente utilizar a [Versão 3.0 (`../v3.0`)](../v3.0)**, que não exige compiladores C++ nem bibliotecas antigas.

---

## 📂 Arquivos desta versão

- [`FaceSafety-2.5-Win.py`](FaceSafety-2.5-Win.py) — Código original para Windows
- [`FaceSafety-2.5-Linx.py`](FaceSafety-2.5-Linx.py) — Código original adaptado para Linux

---

## ⚙️ Como esta versão funcionava (Requisitos Antigos)

A versão 2.5 utilizava a biblioteca `face_recognition` (baseada em `dlib`), que exige compilação C++ no Windows:
1. Python 3.11
2. Visual Studio Build Tools ("Desenvolvimento para desktop com C++")
3. CMake adicionado ao `PATH` do sistema
4. Instalação das dependências:
   ```bash
   pip install dlib face_recognition numpy opencv-python
   ```

---

## 📸 Telas Originais (v2.5)

<p align="center">
  <img src="../.github/readme/telas.png" alt="Telas originais do Face Safety v2.5" width="100%">
</p>
