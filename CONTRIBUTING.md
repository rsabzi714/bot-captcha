# Contributing to MNE Portal Automation Bot

Thank you for your interest in contributing to this project! This guide will help you get started.

## 🚀 Getting Started

### Prerequisites
- Python 3.9 or higher
- Git
- Basic knowledge of web automation and Python

### Development Setup

1. **Fork the repository**
   ```bash
   git clone https://github.com/yourusername/bot-kapcha.git
   cd bot-kapcha
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   playwright install
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## 🛠️ Development Guidelines

### Code Style
- Follow PEP 8 guidelines
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Keep functions small and focused

### Testing
- Test your changes thoroughly before submitting
- Ensure the bot can handle various scenarios
- Test with different browser configurations

### Commit Messages
- Use clear, descriptive commit messages
- Start with a verb (Add, Fix, Update, Remove)
- Keep the first line under 50 characters
- Add detailed description if needed

Example:
```
Add support for new captcha type

- Implement detection for reCAPTCHA v3
- Add fallback mechanism for failed attempts
- Update error handling for timeout scenarios
```

## 🐛 Reporting Issues

When reporting bugs, please include:
- Python version
- Operating system
- Browser type and version
- Steps to reproduce
- Error messages and logs
- Expected vs actual behavior

## 💡 Feature Requests

Before submitting a feature request:
- Check if it already exists in issues
- Explain the use case and benefits
- Consider implementation complexity
- Provide examples if possible

## 🔧 Areas for Contribution

### High Priority
- Improved error handling
- Better captcha detection
- Enhanced stealth features
- Performance optimizations

### Medium Priority
- Additional browser support
- Better logging system
- Configuration improvements
- Documentation updates

### Low Priority
- UI improvements
- Additional notification methods
- Code refactoring
- Test coverage

## 📝 Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow the coding guidelines
   - Add appropriate comments
   - Update documentation if needed

3. **Test thoroughly**
   - Run the bot with your changes
   - Test edge cases
   - Verify no regressions

4. **Submit the pull request**
   - Provide a clear description
   - Reference related issues
   - Include screenshots if applicable

## ⚠️ Important Notes

### Security
- Never commit sensitive information
- Use environment variables for credentials
- Be cautious with proxy configurations
- Respect rate limits and terms of service

### Legal Considerations
- This project is for educational purposes
- Users are responsible for compliance with terms of service
- Respect website policies and rate limits
- Use responsibly and ethically

## 📞 Getting Help

- Check existing issues and documentation
- Join discussions in issues
- Ask questions in pull requests
- Be respectful and patient

## 🙏 Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes for significant contributions
- Project documentation

Thank you for helping improve this project!