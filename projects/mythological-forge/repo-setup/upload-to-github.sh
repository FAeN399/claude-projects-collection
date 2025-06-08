#!/bin/bash
# Script to help upload all projects to the GitHub repository

echo "🚀 Uploading Claude Projects to GitHub Repository"
echo "Repository: https://github.com/FAeN399/claude-projects-collection"
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install git first."
    exit 1
fi

# Create temporary directory for repo
TEMP_DIR="claude-repo-temp"
REPO_URL="https://github.com/FAeN399/claude-projects-collection.git"

echo "📁 Creating temporary directory..."
mkdir -p $TEMP_DIR
cd $TEMP_DIR

# Clone the repository
echo "📥 Cloning repository..."
git clone $REPO_URL .

# Create directory structure
echo "📁 Creating directory structure..."
mkdir -p projects/{mythological-forge,bidirectional-converter,network-standoff}
mkdir -p scripts
mkdir -p docs
mkdir -p shared-tools/{importers,converters,validators,templates}

# Copy README and .gitignore
echo "📄 Adding repository files..."
cp ../README.md .
cp ../.gitignore .

# Create CONTRIBUTING.md
cat > CONTRIBUTING.md << 'EOF'
# Contributing to Claude Projects Collection

Thank you for your interest in contributing!

## How to Contribute

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit your changes** (`git commit -m 'Add amazing feature'`)
4. **Push to the branch** (`git push origin feature/amazing-feature`)
5. **Open a Pull Request**

## Project Guidelines

### Adding a New Project
- Place it in `projects/your-project-name/`
- Include a comprehensive README.md
- Add a setup.py or setup script
- Include requirements.txt if needed
- Add appropriate license

### Code Style
- Follow existing code style in each project
- Add comments for complex logic
- Include docstrings for functions
- Keep security in mind (no hardcoded secrets)

## Reporting Issues
- Use the issue tracker
- Include reproduction steps
- Mention the specific project affected

## License
By contributing, you agree that your contributions will be licensed under the same license as the project.
EOF

# Create main setup script
cat > scripts/setup-all.py << 'EOF'
#!/usr/bin/env python3
"""Setup all Claude projects at once"""

import os
import subprocess
import sys
from pathlib import Path

def setup_all_projects():
    """Install all projects in the collection"""
    print("🔧 Setting up all Claude projects...")
    
    projects_dir = Path("projects")
    successful = []
    failed = []
    
    for project in sorted(projects_dir.iterdir()):
        if project.is_dir():
            setup_file = project / "setup.py"
            requirements_file = project / "requirements.txt"
            
            print(f"\n{'='*60}")
            print(f"📦 Setting up: {project.name}")
            print('='*60)
            
            try:
                os.chdir(project)
                
                # Install requirements if they exist
                if requirements_file.exists():
                    print("📥 Installing requirements...")
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
                
                # Run setup if it exists
                if setup_file.exists():
                    print("🔧 Running setup script...")
                    subprocess.check_call([sys.executable, "setup.py"])
                
                successful.append(project.name)
                print(f"✅ {project.name} setup complete!")
                
            except subprocess.CalledProcessError as e:
                failed.append(project.name)
                print(f"❌ {project.name} setup failed: {e}")
            finally:
                os.chdir("../..")
    
    print("\n" + "="*60)
    print("📊 Setup Summary:")
    print(f"✅ Successful: {len(successful)} projects")
    print(f"❌ Failed: {len(failed)} projects")
    
    if failed:
        print("\nFailed projects:")
        for project in failed:
            print(f"  - {project}")

if __name__ == "__main__":
    setup_all_projects()
EOF

chmod +x scripts/setup-all.py

# Create download single project script
cat > scripts/download-project.py << 'EOF'
#!/usr/bin/env python3
"""Download a single project from the collection"""

import sys
import shutil
import os
from pathlib import Path

def download_project(project_name: str, destination: str = "."):
    """Download a specific project to the destination directory"""
    
    source = Path(f"projects/{project_name}")
    
    if not source.exists():
        print(f"❌ Project '{project_name}' not found")
        print("\nAvailable projects:")
        for p in Path("projects").iterdir():
            if p.is_dir():
                print(f"  - {p.name}")
        return False
    
    dest = Path(destination) / project_name
    
    if dest.exists():
        response = input(f"⚠️  {dest} already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("❌ Download cancelled")
            return False
        shutil.rmtree(dest)
    
    shutil.copytree(source, dest)
    print(f"✅ Downloaded {project_name} to {dest}")
    
    # Check for setup instructions
    readme = dest / "README.md"
    if readme.exists():
        print(f"\n📖 See {readme} for setup instructions")
    
    return True

def main():
    if len(sys.argv) < 2:
        print("Usage: python download-project.py <project-name> [destination]")
        print("\nExample:")
        print("  python download-project.py mythological-forge ~/my-projects")
        sys.exit(1)
    
    project_name = sys.argv[1]
    destination = sys.argv[2] if len(sys.argv) > 2 else "."
    
    download_project(project_name, destination)

if __name__ == "__main__":
    main()
EOF

chmod +x scripts/download-project.py

# Create project template creator
cat > scripts/create-project-template.py << 'EOF'
#!/usr/bin/env python3
"""Create a new project template"""

import os
import sys
from pathlib import Path

def create_project_template(name: str):
    """Create a new project with standard structure"""
    
    project_dir = Path(f"projects/{name}")
    
    if project_dir.exists():
        print(f"❌ Project {name} already exists")
        return False
    
    # Create directories
    project_dir.mkdir(parents=True)
    (project_dir / "src").mkdir()
    (project_dir / "tests").mkdir()
    (project_dir / "docs").mkdir()
    
    # Create README
    with open(project_dir / "README.md", "w") as f:
        f.write(f"""# {name.replace('-', ' ').title()}

## Description
Brief description of what this project does.

## Features
- Feature 1
- Feature 2
- Feature 3

## Installation
```bash
cd projects/{name}
pip install -r requirements.txt
python setup.py
```

## Usage
```python
# Example usage
```

## Configuration
Describe any configuration needed.

## License
MIT License - See LICENSE file for details.
""")
    
    # Create setup.py
    with open(project_dir / "setup.py", "w") as f:
        f.write(f"""#!/usr/bin/env python3
\"\"\"Setup script for {name}\"\"\"

import os
from pathlib import Path

def setup():
    print("Setting up {name}...")
    
    # Create necessary directories
    dirs = ['data', 'output', 'config']
    for d in dirs:
        Path(d).mkdir(exist_ok=True)
    
    print("✅ Setup complete!")

if __name__ == "__main__":
    setup()
""")
    
    # Create requirements.txt
    with open(project_dir / "requirements.txt", "w") as f:
        f.write("# Add your requirements here\n")
    
    # Create LICENSE
    with open(project_dir / "LICENSE", "w") as f:
        f.write("""MIT License

Copyright (c) 2024 Claude Projects Collection

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
""")
    
    print(f"✅ Created project template: {name}")
    print(f"📁 Location: {project_dir}")
    return True

def main():
    if len(sys.argv) < 2:
        print("Usage: python create-project-template.py <project-name>")
        sys.exit(1)
    
    create_project_template(sys.argv[1])

if __name__ == "__main__":
    main()
EOF

chmod +x scripts/create-project-template.py

echo ""
echo "✅ Repository structure created!"
echo ""
echo "📋 Next steps:"
echo "1. Copy your project files to the appropriate directories:"
echo "   - The Mythological Forge → projects/mythological-forge/"
echo "   - VML Converter → projects/bidirectional-converter/"
echo "   - Network Standoff → projects/network-standoff/"
echo ""
echo "2. Stage and commit changes:"
echo "   git add ."
echo "   git commit -m 'Initial repository setup with all Claude projects'"
echo ""
echo "3. Push to GitHub:"
echo "   git push origin main"
echo ""
echo "Need help with the next steps? Just ask!"