<p align="center">
  <img src=".github/readme/banner.png" alt="FaceSafety" width="100%">
</p>

<p align="center">
  <img alt="👤 Projeto pessoal" src="https://img.shields.io/badge/%F0%9F%91%A4_Projeto_pessoal-6E40C9?style=for-the-badge">
  <img alt="Python" src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white">
  <img alt="OpenCV" src="https://img.shields.io/badge/OpenCV-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white">
</p>

<p align="center">
  <b>Face Safety</b>: sistema de cadastro de rostos, reconhecimento facial em tempo real e controle de acesso em Python (Windows, Linux, macOS e Raspberry Pi).
</p>

<p align="center">
  <a href="English%20version.md">🇺🇸 English Version</a> ·
  <a href="#-executar-1-clique-windows-exe">🪄 Baixar .EXE (1 Clique)</a> ·
  <a href="#-como-rodar-o-código-fonte-v30">⚡ Rodar em Python</a> ·
  <a href="#️-função-key-controle-de-acesso">🗝️ Função KEY</a> ·
  <a href="#️-a-história-do-projeto-legado-vs-nova-geração">🏛️ O Legado</a>
</p>

---

# 🏛️ A História do Projeto: Legado vs. Nova Geração

O **Face Safety** nasceu na época da faculdade como o meu **primeiro código sério em Python**, feito **100% à mão, antes da era das IAs**, na base de muita pesquisa, leitura de documentações e testes práticos.

Com o passar dos anos, as bibliotecas originais (`dlib` e `face_recognition`) passaram a exigir compiladores C++ pesados (Visual Studio Build Tools e CMake), dificultando a instalação para quem queria testar ou estudar o projeto hoje.

Para **manter o legado vivo** sem apagar a história original, o repositório agora está organizado em duas pastas:

| Pasta | Descrição |
| :--- | :--- |
| 🚀 **[`v3.0/`](v3.0/)** *(Recomendada)* | **Versão Moderna (3.0):** Recriada com métodos recentes usando o motor neural nativo do OpenCV (**YuNet + SFace ONNX**). Não precisa de `dlib`, `CMake` nem `Visual Studio`. Inclui interface moderna Dark UI com câmera integrada e versão **`.exe` pronta para abrir**! |
| 🏛️ **[`v2.5-legado/`](v2.5-legado/)** | **Versão Clássica da Faculdade (2.5):** O código original histórico (`FaceSafety-2.5-Win.py` e `FaceSafety-2.5-Linx.py`), preservado exatamente como foi escrito à mão na época. |

---

# 🪄 Executar no Windows (3 Formas Opcionais!)

Você pode escolher a forma que achar mais prática:

### Opção A: Inicializador Automático (`.bat`) — *Mais prático!*
Basta dar dois cliques no arquivo **[`Iniciar-FaceSafety.bat`](Iniciar-FaceSafety.bat)** na raiz do projeto. Ele abre um menu interativo em que você escolhe:
- **`[1]`** Abrir direto a versão pronta **`.EXE`** (sem precisar de Python).
- **`[2]`** Verificar/instalar o `opencv-python` automaticamente e rodar o código-fonte **`.py`** (ideal se você editou a função `key()`).
- **`[3]`** Criar um ambiente virtual (`venv`) limpo com `--no-cache-dir`, instalar tudo sozinho e abrir o programa (evita qualquer erro de permissão no Windows).
- **`[4]`** Abrir o `facesafety.py` direto no Bloco de Notas para editar a função `key()`.

### Opção B: Executável Direto 1-Clique (`.exe`)
Quer apenas abrir o programa direto **sem instalar Python e sem digitar nada no terminal**?
1. Acesse a pasta [`v3.0/`](v3.0/) e execute o arquivo **[`FaceSafety-v3.0.exe`](v3.0/FaceSafety-v3.0.exe)**.
2. Na primeira vez que abrir, ele criará automaticamente a pasta `dados/` ao lado do programa e baixará os modelos leves de reconhecimento facial.

> ⚠️ **Observação:** Na versão `.exe` o código já está compilado, então não é possível editar a função `key()` dentro dele. Se quiser personalizar a função `key()`, use a Opção A (`[2]`/`[3]`) ou a Opção C abaixo!

---

# ⚡ Opção C: Rodar pelo Código-Fonte no Terminal (Windows, Linux, macOS e Raspberry Pi)

Na versão **3.0**, você não precisa instalar nenhum compilador C++. Basta ter o **Python 3.9+** instalado e rodar no terminal:

```bash
cd v3.0
pip install -r requirements.txt
python facesafety.py
```

Pronto! Apenas o `opencv-python` e o `numpy` são instalados, e os modelos neurais ONNX são baixados automaticamente na primeira execução.

---

# 🔬 Como Usar o Face Safety 3.0

Tudo funciona em uma **única janela moderna** com a câmera embutida:

1. **➕ Cadastrar Pessoa:**
   - Digite o nome da pessoa no painel lateral direito.
   - *(Opcional)* Marque **"Cadastrar como Administrador"** caso ela deva acionar a função `key()`.
   - Clique em **📸 Capturar da Câmera** para tirar a foto na hora, ou em **📁 Foto...** para escolher uma imagem já salva no computador.
   - O sistema valida automaticamente se há um rosto nítido antes de salvar, evitando cadastros corrompidos!
2. **👥 Gerenciar Pessoas e Administradores (`ADM`):**
   - Todos os rostos cadastrados aparecem na lista lateral indicando se são `⭐ [ADM]` ou `👤` comuns.
   - Selecione qualquer pessoa na lista e clique em **⭐ + / - ADM** para promover ou remover permissão de Administrador instantaneamente.
   - Clique em **🗑️ Remover** para apagar o cadastro selecionado.
3. **▶ Ligar Câmera / Scanner:**
   - Clique em **▶ Ligar Câmera / Scanner** para iniciar o reconhecimento em tempo real:
     - 🟨 **Quadro Dourado `[ADM]`**: Administrador reconhecido (aciona a função `key()` automaticamente).
     - 🟩 **Quadro Verde**: Pessoa cadastrada reconhecida (exibe nome e porcentagem de confiança).
     - 🟥 **Quadro Vermelho**: Rosto não cadastrado (`Nao Cadastrado`).

---

# 🗝️ Função `key()` (Controle de Acesso)

Pensada para quem deseja integrar o reconhecimento facial com **fechaduras eletrônicas, relés, Raspberry Pi (GPIO), Arduino (Serial) ou sistemas de monitoramento**.

No final do arquivo [`v3.0/facesafety.py`](v3.0/facesafety.py), você encontra a função `key(nome)`:

```python
def key(nome: str = ""):
    print(f"[KEY] Acesso permitido para ADM '{nome}' por 5 segundos...")

    # 1) Coloque abaixo seu código para liberar o acesso (ex: destrancar porta / ligar relé)
    pass

    # Tempo em que o acesso permanece liberado (em segundos)
    time.sleep(5)

    print(f"[KEY] Acesso expirado após 5 segundos para '{nome}'.")

    # 2) Coloque abaixo seu código para encerrar o acesso (ex: trancar porta / desligar relé)
    pass
```

- Sempre que um **Administrador (`ADM`)** entra na frente da câmera, o programa executa a função `key(nome)` automaticamente.
- Na versão 3.0, ela roda em **segundo plano (thread separada)** com trava contra repetições simultâneas — assim o `time.sleep(5)` **não congela o vídeo da câmera**!

---

# 📸 Telas da Versão Clássica (v2.5 Legado)

Registros da interface original criada na época da faculdade (código disponível em [`v2.5-legado/`](v2.5-legado/)):

<p align="center">
  <img src=".github/readme/telas.png" alt="Telas originais do FaceSafety v2.5" width="100%">
</p>

---

# 📬 Contato e Suporte

Encontrou algum problema ou quer trocar uma ideia sobre o projeto?
- 🐛 **GitHub Issues:** [Abrir uma Issue no repositório](https://github.com/Davicjc/Face-Safety/issues) *(recomendado para dúvidas técnicas)*
- 📧 **E-mail:** `contato@davicjc.com` / `davicjc@gmail.com`
- 💬 **Telegram:** [@Davicjc](https://t.me/Davicjc)

---

<p align="center">Feito por <a href="https://github.com/Davicjc">Davi Castro</a> · <a href="https://davicjc.com">davicjc.com</a></p>
