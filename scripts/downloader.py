import json
import requests
import yaml
from pathlib import Path
from datetime import datetime

class SmartDownloader:
    def __init__(self):
        self.temp_dir = Path('temp_downloads')
        self.temp_dir.mkdir(exist_ok=True)
        
        with open('sources.yaml', 'r') as f:
            self.sources = yaml.safe_load(f)
        
        self.index = {"updated": str(datetime.now()), "software": {}}
        self.release_notes = []
    
    def get_latest_github_release(self, repo):
        """Get latest release info from GitHub"""
        url = f"https://api.github.com/repos/{repo}/releases/latest"
        resp = requests.get(url)
        resp.raise_for_status()
        return resp.json()
    
    def download_file(self, url, filename):
        """Download file to temp directory"""
        filepath = self.temp_dir / filename
        print(f"Downloading {filename}...")
        
        resp = requests.get(url, stream=True)
        resp.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=1024*1024):
                f.write(chunk)
        
        return filepath
    
    def process_all_sources(self):
        """Download all configured software"""
        for category, items in self.sources.items():
            self.index["software"][category] = []
            
            for item in items:
                try:
                    if item['type'] == 'github':
                        self.process_github_source(item, category)
                    elif item['type'] == 'direct':
                        self.process_direct_source(item, category)
                except Exception as e:
                    print(f"Error processing {item['name']}: {e}")
    
    def process_github_source(self, item, category):
        """Process GitHub release source"""
        release = self.get_latest_github_release(item['repo'])
        version = release['tag_name']
        
        # Check for updates
        if self.is_new_version(item['name'], version):
            for asset in release['assets']:
                if self.should_download_asset(asset['name'], item.get('pattern')):
                    filepath = self.download_file(
                        asset['browser_download_url'],
                        f"{item['name']}_{version}_{asset['name']}"
                    )
                    
                    self.index["software"][category].append({
                        "name": item['name'],
                        "version": version,
                        "file": filepath.name,
                        "size": asset['size'],
                        "download_url": asset['browser_download_url']
                    })
                    
                    self.release_notes.append(
                        f"- **{item['name']}** updated to {version}"
                    )
    
    def should_download_asset(self, filename, pattern):
        """Check if asset matches pattern"""
        if not pattern:
            return True
        if isinstance(pattern, list):
            return any(p in filename.lower() for p in pattern)
        return pattern in filename.lower()
    
    def is_new_version(self, software, version):
        """Check if this is a new version"""
        # Load previous index if exists
        try:
            with open('index.json', 'r') as f:
                old_index = json.load(f)
                # Check old versions logic here
                return True  # Simplified
        except:
            return True
    
    def save_outputs(self):
        """Save index and release notes"""
        with open('index.json', 'w') as f:
            json.dump(self.index, f, indent=2)
        
        with open('release_notes.md', 'w') as f:
            f.write("## Updates\n\n")
            f.write('\n'.join(self.release_notes) if self.release_notes 
                   else "No updates in this run")

if __name__ == "__main__":
    downloader = SmartDownloader()
    downloader.process_all_sources()
    downloader.save_outputs()