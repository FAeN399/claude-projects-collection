# Quick Setup: Copy & Run Commands

## 🚀 Method 1: PowerShell Script (For Windows)

Copy and save this as `setup-mythforge.ps1`:

```powershell
# The Mythological Forge - Quick Setup Script
Write-Host "🔥 Setting up The Mythological Forge..." -ForegroundColor Cyan

# Create directory structure
$directories = @(
    "content\stories\by-origin\greek",
    "content\stories\by-origin\norse", 
    "content\stories\by-origin\egyptian",
    "content\stories\by-origin\celtic",
    "content\stories\by-origin\modern",
    "content\stories\by-type\creation",
    "content\stories\by-type\hero-journey",
    "content\stories\by-type\transformation",
    "content\stories\by-theme\consciousness",
    "content\characters\deities",
    "content\characters\heroes",
    "content\pantheons",
    "content\collections",
    "content\html-stories\modern",
    "content\media\images",
    "metadata\catalogs",
    "metadata\indexes", 
    "metadata\schemas",
    "templates",
    "tools\import",
    "tools\validate",
    "database\backups"
)

foreach ($dir in $directories) {
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
}
Write-Host "✓ Directories created" -ForegroundColor Green

# Download files from GitHub Gist or create inline
Write-Host "📥 Creating files..." -ForegroundColor Yellow

# Create requirements.txt
@"
beautifulsoup4>=4.12.0
html2text>=2020.1.16
pyyaml>=6.0
jsonschema>=4.0
"@ | Out-File -FilePath "requirements.txt" -Encoding UTF8

Write-Host "✓ Files created" -ForegroundColor Green
Write-Host "🎉 Setup complete! Next: pip install -r requirements.txt" -ForegroundColor Cyan
```

## 🚀 Method 2: Single cURL Command (For Linux/Mac)

```bash
# Download and run setup script from a GitHub Gist
curl -L https://gist.github.com/YOUR_GIST_ID/raw/setup-mythforge.sh | bash
```

## 🚀 Method 3: Git Clone (Fastest)

I can create a GitHub repository with all these files:

```bash
# Clone the entire project
git clone https://github.com/yourusername/mythological-forge-setup.git
cd mythological-forge-setup

# Run setup
./setup.sh  # or setup.bat for Windows
```

## 🚀 Method 4: Download as ZIP

1. I'll create all files in a GitHub repo
2. Use GitHub's "Download ZIP" button
3. Extract and run setup script

## 🚀 Method 5: Python One-Liner

```python
# Download and setup with one Python command
python -c "import urllib.request; exec(urllib.request.urlopen('https://gist.github.com/YOUR_GIST/raw/setup.py').read())"
```

## 📦 Best Option: GitHub Repository

Would you like me to:
1. Create a complete GitHub repository structure with all the files?
2. Create a Gist with a single setup script that creates all files?
3. Create a downloadable ZIP with everything?

The GitHub repo would be the most efficient because you could:
- Clone it once: `git clone [repo-url]`
- Get updates easily: `git pull`
- See all files organized properly
- Use GitHub's web interface to browse

## 💡 Alternative: Browser Extension

There are browser extensions like:
- **Copy All Code Blocks** - Copies all code from a page
- **ChatGPT/Claude Exporter** - Exports entire conversations
- **Markdown Web Clipper** - Saves formatted content

## 🎯 Recommended Approach

1. **For immediate use**: Run the bundler script I created:
   ```bash
   python download_bundle.py
   ```
   This creates one file with everything inside.

2. **For long-term**: Set up a GitHub repository with all the files.

3. **For sharing**: Create a Gist or repo others can clone.

Which method would work best for your workflow?