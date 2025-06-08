# Claude Projects Collection

A comprehensive collection of projects, tools, and systems generated through conversations with Claude.

## 🌟 Featured Projects

### [The Mythological Forge](projects/mythological-forge/)
*Transform mythological narratives with AI-assisted storytelling*
- 📚 Content management system for myths and legends
- 🎭 Dual HTML/Markdown format support
- 🔍 Advanced search and categorization
- ✨ Beautiful cosmic-themed UI

### [Bidirectional Converter with VML](projects/bidirectional-converter/)
*Convert between natural language and code with custom markup support*
- 🔄 Two-way text-to-code conversion
- 📝 VML (Versatile Markup Language) support
- 🤖 Claude API integration
- 🎨 Enhanced editor with syntax highlighting

### [Network Standoff Hub](projects/network-standoff/)
*AI hub setup guides and configurations*
- 🏠 Home server configurations
- 🐳 Docker compositions
- 🔧 Setup automation scripts
- 📖 Comprehensive guides

## 🚀 Quick Start

### Clone and Setup Everything
```bash
git clone https://github.com/FAeN399/claude-projects-collection.git
cd claude-projects-collection
python scripts/setup-all.py
```

### Get a Single Project
```bash
# Method 1: Using our download script
python scripts/download-project.py mythological-forge

# Method 2: Using git sparse-checkout
git clone --filter=blob:none --sparse https://github.com/FAeN399/claude-projects-collection.git
cd claude-projects-collection
git sparse-checkout add projects/mythological-forge
```

## 📦 Project Categories

- **🎭 Content Management**: Mythological Forge, Story Organizers
- **🔧 Development Tools**: Converters, Formatters, Validators  
- **🤖 AI Integration**: API wrappers, Prompt managers
- **🏗️ Infrastructure**: Server setups, Docker configs
- **✨ Creative Tools**: Narrative generators, World builders

## 📊 Project Status

| Project | Status | Description | Setup |
|---------|--------|-------------|-------|
| Mythological Forge | ✅ Active | Mythological content management | [Setup](projects/mythological-forge/README.md) |
| VML Converter | ✅ Active | Bidirectional text/code converter | [Setup](projects/bidirectional-converter/README.md) |
| Network Hub | ✅ Active | AI server setup guides | [Setup](projects/network-standoff/README.md) |

## 🛠️ Development

### Adding a New Project
1. Fork this repository
2. Create your project in `projects/your-project-name/`
3. Include a README.md and setup script
4. Submit a pull request

### Project Structure Requirements
```
projects/your-project/
├── README.md           # Project description and usage
├── setup.py           # Automated setup script
├── requirements.txt   # Python dependencies (if applicable)
├── LICENSE           # Project license
└── src/              # Source code
```

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Ways to Contribute
- 🐛 Report bugs and issues
- 💡 Suggest new features
- 🔧 Submit bug fixes
- 📚 Improve documentation
- ⭐ Star the repository

## 📄 License

Each project may have its own license. See individual project directories for specific license information. The repository structure and setup scripts are MIT licensed.

## 🙏 Acknowledgments

- All projects generated through conversations with Claude (Anthropic)
- Community contributors and testers
- Open source libraries used in various projects

---

*Created with 💜 by the Claude + Human collaboration*