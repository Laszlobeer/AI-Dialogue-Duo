# 🤖 AI Dialogue Duo (Ollama Edition)

Welcome to **AI Dialogue Duo**, now exclusively powered only by [Ollama](https://ollama.com)! This Flask-based app uses two Ollama models to engage in real-time conversations on any topic.


[![Buy Me a Coffee](https://img.shields.io/badge/☕️-Buy%20Me%20a%20Coffee-yellow?style=flat\&logo=ko-fi)](https://ko-fi.com/laszlobeer)

---
### 🎬 Preview



![Demo](video/Screen%20Capture_select-area_20250623231153.gif)



## 🚀 Features

* **Dual Ollama Conversations**: Choose any two Ollama-compatible models to converse.
* **Real-Time Streaming**: Conversations stream live via Server-Sent Events (SSE).
* **Customizable Turns**: Define how many back-and-forth exchanges each model makes.
* **Theme Support**: Toggle between light, slate, sand, mist, and charcoal themes.
* **Responsive Design**: Mobile-optimized for seamless experience on any device.

## 🛠️ Prerequisites

* **Ollama CLI**: Make sure you have the [Ollama CLI](https://ollama.com/docs/cli-install) installed and authenticated.
* **Python 3.8+**

## ⚙️ Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/Laszlobeer/AI-Dialogue-Duo.git
   cd AI-Dialogue-Duo
   ```

2. **Install Python dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Install Ollama models**

   ```bash
   ollama pull <model-name-1>
   ollama pull <model-name-2>
   ```

4. **Run the app**

   ```bash
   python app.py
   ```

5. **Open Your Browser**

   * Local: `http://localhost:9000`
   * Network: `http://<your-local-ip>:9000`

## 🧩 Usage

1. Select two Ollama models from the dropdown menus.
2. Enter your desired discussion topic.
3. Set the number of turns per model.
4. Click **Start Discussion** to initiate the conversation.
5. Use **Refresh Models** to reload available Ollama models.

## 🤝 Contributing

Contributions are welcome! You can:

* Submit issues or feature requests.
* Fork the repo and open pull requests.
* Enhance themes, UI, or core functionality.



## 🧰 Configuration

Before running the app, ensure you have configured your Ollama endpoint and authentication (if required):

* **OLLAMA\_HOST**: URL of your Ollama server (default: `http://localhost:11434`).
* **OLLAMA\_API\_KEY**: (Optional) API key or token, if your Ollama instance requires authentication.

You can export these in your shell:

```bash
export OLLAMA_HOST=http://localhost:11434
export OLLAMA_API_KEY=<your-api-key>
```


---

## 💖 Support

If you enjoy this project, consider buying me a coffee:

[![Buy Me a Coffee](https://img.shields.io/badge/☕️-Buy%20Me%20a%20Coffee-yellow?style=flat\&logo=ko-fi)](https://ko-fi.com/laszlobeer)

Thank you for your support! 😊

