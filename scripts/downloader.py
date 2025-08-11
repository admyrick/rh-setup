import json
import requests
import re
from bs4 import BeautifulSoup
from pathlib import Path
from datetime import datetime
import hashlib

class UniversalDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.temp_dir = Path('downloads')
        self.temp_dir.mkdir(exist_ok=True)
    
    def download_from_direct_url(self, url, filename=None):
        """Download from direct URL"""
        if not filename:
            filename = url.split('/')[-1]
        
        filepath = self.temp_dir / filename
        print(f"Downloading from {url}")
        
        resp = self.session.get(url, stream=True)
        resp.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return filepath
    
    def download_from_sourceforge(self, project, filename_pattern=None):
        """Download from SourceForge"""
        # Get latest file URL
        rss_url = f"https://sourceforge.net/projects/{project}/rss?path=/"
        resp = self.session.get(rss_url)
        
        # Parse RSS for latest file
        import xml.etree.ElementTree as ET
        root = ET.fromstring(resp.content)
        
        for item in root.findall('.//item'):
            link = item.find('link').text
            if filename_pattern and filename_pattern not in link:
                continue
            
            # SourceForge download URL
            download_url = link.replace('/files/', '/projects/').replace('/download', '')
            download_url = f"{download_url}/download"
            
            filename = link.split('/')[-2]
            return self.download_from_direct_url(download_url, filename)
    
    def scrape_download_link(self, page_url, link_pattern):
        """Scrape a webpage for download links"""
        resp = self.session.get(page_url)
        soup = BeautifulSoup(resp.content, 'html.parser')
        
        # Find all links matching pattern
        for link in soup.find_all('a', href=True):
            href = link['href']
            if re.search(link_pattern, href):
                # Make absolute URL if relative
                if not href.startswith('http'):
                    from urllib.parse import urljoin
                    href = urljoin(page_url, href)
                
                return self.download_from_direct_url(href)
        
        raise ValueError(f"No download link found matching {link_pattern}")
    
    def download_gitlab_release(self, project_id, filename_pattern=None):
        """Download from GitLab releases"""
        url = f"https://gitlab.com/api/v4/projects/{project_id}/releases"
        resp = self.session.get(url)
        releases = resp.json()
        
        if releases:
            latest = releases[0]
            for link in latest.get('assets', {}).get('links', []):
                if filename_pattern and filename_pattern not in link['name']:
                    continue
                return self.download_from_direct_url(link['url'], link['name'])
    
    def download_from_fosshub(self, app_name):
        """Download from FossHub"""
        # FossHub requires special handling
        page_url = f"https://www.fosshub.com/{app_name}.html"
        # Would need to handle their JavaScript-based downloads
        pass
    
    def download_from_github_direct(self, url):
        """Download non-release files from GitHub (like raw files)"""
        # Convert to raw URL if needed
        if 'github.com' in url and '/blob/' in url:
            url = url.replace('github.com', 'raw.githubusercontent.com')
            url = url.replace('/blob/', '/')
        
        return self.download_from_direct_url(url)