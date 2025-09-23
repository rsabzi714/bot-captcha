# 🤖 MNE Portal Automation Bot

An advanced automation bot for the Portuguese Ministry of Foreign Affairs (MNE) portal with sophisticated anti-detection capabilities.

## ✨ Key Features

- 🔒 **Advanced Stealth**: Modern anti-detection techniques
- 🤖 **Human Behavior Simulation**: Realistic user interaction patterns  
- 🌐 **Residential Proxy Support**: Legitimate IP addresses
- 🧩 **CAPTCHA Solving**: Integrated with 2Captcha service
- 📱 **Telegram Notifications**: Real-time alerts and updates
- 🔄 **Session Management**: Persistent authentication state
- 🛡️ **Error Handling**: Robust error recovery mechanisms
- 📊 **Comprehensive Logging**: Detailed operation tracking

## 🚀 Quick Start

### Prerequisites
- Python 3.9 or higher
- Git
- 2Captcha account (for CAPTCHA solving)
- Telegram bot (for notifications)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd bot-kapcha
```

2. **Create virtual environment**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
playwright install
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env file with your credentials
```

5. **Run the bot**
```bash
python main.py
```

## ⚙️ Configuration

### 1. 2Captcha Setup
- Register at [2captcha.com](https://2captcha.com)
- Get your API key
- Add funds to your account

### 2. Telegram Bot Setup
- Create a bot via [@BotFather](https://t.me/botfather)
- Get your Bot Token
- Get your Chat ID

### 3. Proxy Configuration (Optional)
- Choose a provider (Bright Data, Smartproxy, etc.)
- Get connection details
- Configure in `.env` file

### 4. Environment Variables
Create a `.env` file with the following variables:

```env
# MNE Portal Credentials
MNE_USERNAME=your_username
MNE_PASSWORD=your_password

# 2Captcha API Key
CAPTCHA_API_KEY=your_2captcha_api_key

# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Proxy Settings (Optional)
PROXY_HOST=proxy.example.com
PROXY_PORT=3128
PROXY_USERNAME=proxy_user
PROXY_PASSWORD=proxy_pass

# Browser Type
BROWSER_TYPE=chromium
```

## 📁 Project Structure

```
bot-kapcha/
├── core/                    # Core bot functionality
│   ├── bot_manager.py      # Main bot manager
│   ├── login_handler.py    # Login automation
│   └── session_manager.py  # Session management
├── modules/                 # Feature modules
│   ├── captcha_handler.py  # CAPTCHA solving
│   ├── form_automation.py  # Form interactions
│   └── monitoring.py       # System monitoring
├── browser/                 # Browser management
│   ├── browser_launcher.py # Browser initialization
│   ├── stealth_injector.py # Anti-detection
│   └── viewport_manager.py # Viewport handling
├── utils/                   # Utility functions
│   ├── element_finder.py   # Element location
│   ├── error_handler.py    # Error management
│   └── page_detector.py    # Page detection
├── config.py               # Configuration settings
├── human_behavior.py       # Human behavior simulation
├── proxy_manager.py        # Proxy management
├── telegram_notifier.py    # Telegram notifications
├── main.py                 # Entry point
├── requirements.txt        # Dependencies
└── .env.example           # Environment template
```

## 🚀 Deployment

### Local Development
```bash
# Run in development mode
python main.py
```

### Production Deployment (Linux VPS)

1. **Upload files**
```bash
scp -r bot-kapcha/ user@your-vps:/home/user/
```

2. **Setup environment**
```bash
ssh user@your-vps
cd bot-kapcha
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install
```

3. **Create systemd service**
```bash
sudo nano /etc/systemd/system/mne-bot.service
```

```ini
[Unit]
Description=MNE Portal Bot
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/home/your-username/bot-kapcha
Environment=PATH=/home/your-username/bot-kapcha/venv/bin
ExecStart=/home/your-username/bot-kapcha/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

4. **Enable service**
```bash
sudo systemctl daemon-reload
sudo systemctl enable mne-bot
sudo systemctl start mne-bot
```

## 📊 Monitoring

### View logs
```bash
# Service logs
sudo journalctl -u mne-bot -f

# Application logs
tail -f mne_bot.log
```

### Check status
```bash
sudo systemctl status mne-bot
```

## ⚠️ Important Notes

**Security Guidelines:**
- Never commit sensitive data to the repository
- Use environment variables for all credentials
- Regularly test proxy connections
- Monitor logs for unusual activity

**Pre-deployment Checklist:**
- [ ] Python 3.9+ installed
- [ ] All dependencies installed
- [ ] `.env` file configured
- [ ] Proxy tested (if using)
- [ ] 2Captcha account funded
- [ ] Telegram bot tested

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is for educational purposes only. Use at your own responsibility.

## ⚡ Features in Development

- [ ] Multi-account support
- [ ] Advanced scheduling
- [ ] Web dashboard
- [ ] Docker containerization
- [ ] Cloud deployment guides