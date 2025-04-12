"""
Project Scanner - Finds and analyzes code projects in a directory.
"""
import os
import time
import logging
from datetime import datetime
from pathlib import Path
import yaml
import git
from git.exc import InvalidGitRepositoryError, NoSuchPathError
from dataclasses import dataclass, field, asdict
import json
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('project_scanner')

@dataclass
class Project:
    """Class representing a code project."""
    name: str
    path: str
    is_git_repo: bool = False
    created_date: str = ""
    modified_date: str = ""
    last_commit_date: Optional[str] = None
    commit_frequency: float = 0.0  # commits per week
    status: str = "Unknown"
    total_commits: int = 0
    languages: Dict[str, int] = field(default_factory=dict)
    
    # New Git-specific fields
    current_branch: str = ""
    uncommitted_changes: int = 0
    untracked_files: int = 0
    ahead_count: int = 0
    behind_count: int = 0
    branches: List[str] = field(default_factory=list)
    recent_commits: List[Dict[str, str]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert object to dictionary."""
        return asdict(self)

class ProjectScanner:
    """Scans directories for code projects and analyzes them."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize with config file path."""
        logger.info(f"Initializing ProjectScanner with config: {config_path}")
        
        # Load configuration
        with open(config_path, 'r') as config_file:
            self.config = yaml.safe_load(config_file)
        
        self.root_dir = Path(self.config['scan_directory'])
        self.markers = self.config['project_markers']
        self.thresholds = self.config['thresholds']
        
        # Add excluded directories
        self.excluded_dirs = ['.git', '.venv', 'venv', 'env', '__pycache__', 'node_modules']
        
        logger.info(f"Root directory set to: {self.root_dir}")
        logger.info(f"Using markers: {self.markers}")
    
    def scan_directory(self) -> List[Project]:
        """
        Scan the root directory for code projects.
        Returns a list of Project objects.
        """
        if not self.root_dir.exists():
            logger.error(f"Root directory does not exist: {self.root_dir}")
            return []
        
        projects = []
        logger.info(f"Starting scan of {self.root_dir}")
        
        for item in self.root_dir.glob('**/*'):
            # Skip hidden directories, non-directories, and excluded directories
            if not item.is_dir() or item.name.startswith('.'):
                continue
            
            # Skip excluded directories
            if any(excluded in str(item) for excluded in self.excluded_dirs):
                continue
                
            # Skip directories inside project directories we've already identified
            already_in_project = False
            for project in projects:
                if str(item).startswith(project.path):
                    already_in_project = True
                    break
            
            if already_in_project:
                continue
            
            # Check if this directory contains any project markers
            if self._is_project_directory(item):
                logger.info(f"Found project: {item.name} at {item}")
                project = self._create_project(item)
                projects.append(project)
        
        logger.info(f"Scan completed. Found {len(projects)} projects.")
        return projects
    
    def _is_project_directory(self, directory: Path) -> bool:
        """
        Check if the directory is a code project.
        Returns True if directory contains any of the marker files/dirs.
        """
        for marker in self.markers:
            if (directory / marker).exists():
                return True
        return False
    
    def _create_project(self, directory: Path) -> Project:
        """Create a Project object with metadata from the directory."""
        # Get basic file stats
        created_date = datetime.fromtimestamp(directory.stat().st_ctime)
        modified_date = datetime.fromtimestamp(directory.stat().st_mtime)
        
        # Initialize the project
        project = Project(
            name=directory.name,
            path=str(directory),
            created_date=created_date.isoformat(),
            modified_date=modified_date.isoformat()
        )
        
        # Check if it's a git repository
        git_dir = directory / ".git"
        if git_dir.exists():
            project.is_git_repo = True
            self._analyze_git_repo(project)
        
        # Classify project status
        self._classify_project(project)
        
        return project
    
    def _analyze_git_repo(self, project: Project) -> None:
        """
        Analyze a git repository and update project with git stats.
        """
        try:
            repo = git.Repo(project.path)
            
            # Basic commit info
            try:
                commits = list(repo.iter_commits())
                project.total_commits = len(commits)
                
                if commits:
                    # Get the latest commit date
                    latest_commit = commits[0]
                    project.last_commit_date = datetime.fromtimestamp(
                        latest_commit.committed_date
                    ).isoformat()
                    
                    # Calculate commit frequency (commits per week)
                    if len(commits) > 1:
                        first_commit = commits[-1]
                        time_span = latest_commit.committed_date - first_commit.committed_date
                        weeks = max(1, time_span / (7 * 24 * 3600))
                        project.commit_frequency = project.total_commits / weeks
                    
                    # Get recent commits
                    project.recent_commits = [
                        {
                            'hash': str(c.hexsha)[:8],
                            'message': c.message.split('\n')[0],
                            'author': c.author.name,
                            'date': datetime.fromtimestamp(c.committed_date).isoformat()
                        }
                        for c in commits[:5]  # Last 5 commits
                    ]
                
                # Get current branch and all branches
                project.current_branch = repo.active_branch.name
                project.branches = [b.name for b in repo.branches]
                
                # Get status info
                if not repo.bare:
                    # Count uncommitted changes
                    project.uncommitted_changes = len(repo.index.diff(None))
                    
                    # Count untracked files
                    project.untracked_files = len(repo.untracked_files)
                    
                    # Get ahead/behind counts if we have a remote
                    if len(repo.remotes) > 0:
                        try:
                            remote = repo.remotes.origin
                            remote.fetch()
                            ahead_behind = repo.iter_commits('origin/main..main')
                            project.ahead_count = sum(1 for _ in ahead_behind)
                            behind_behind = repo.iter_commits('main..origin/main')
                            project.behind_count = sum(1 for _ in behind_behind)
                        except Exception as e:
                            logger.warning(f"Error getting remote status: {str(e)}")
                
            except Exception as e:
                logger.warning(f"Error analyzing commits for {project.path}: {str(e)}")
                
        except (InvalidGitRepositoryError, NoSuchPathError) as e:
            logger.warning(f"Error accessing git repository at {project.path}: {str(e)}")
            project.is_git_repo = False
    
    def _classify_project(self, project: Project) -> None:
        """
        Classify the project based on its activity.
        """
        if not project.is_git_repo or not project.last_commit_date:
            project.status = "Unknown"
            return
        
        # Calculate days since last commit
        last_commit = datetime.fromisoformat(project.last_commit_date)
        days_since_commit = (datetime.now() - last_commit).days
        
        # Classify based on thresholds
        if days_since_commit <= self.thresholds['active']:
            project.status = "Active"
        elif days_since_commit <= self.thresholds['dormant']:
            project.status = "Dormant"
        elif days_since_commit <= self.thresholds['abandoned']:
            project.status = "Inactive"
        else:
            project.status = "Abandoned"
        
    def get_projects_json(self) -> str:
        """
        Scan for projects and return data as JSON string.
        """
        projects = self.scan_directory()
        return json.dumps([p.to_dict() for p in projects], indent=2)

if __name__ == "__main__":
    # Simple test to run the scanner directly
    scanner = ProjectScanner()
    projects = scanner.scan_directory()
    
    print(f"Found {len(projects)} projects:")
    for project in projects:
        print(f"- {project.name} ({project.status})")
        print(f"  Path: {project.path}")
        if project.is_git_repo:
            print(f"  Last commit: {project.last_commit_date}")
            print(f"  Commit frequency: {project.commit_frequency:.2f} per week")
        print("") 