"""
Project Tracker - Main application entry point.

This tool helps you track and manage your coding projects by scanning directories,
analyzing git repositories, and displaying project information in a web dashboard.
"""
import os
import sys
import logging
import yaml
import argparse
from pathlib import Path
from app import create_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('main')

def main():
    """Main entry point for the application."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Project Tracker - Monitor and manage your coding projects')
    parser.add_argument('--config', type=str, default='config.yaml', help='Path to configuration file')
    parser.add_argument('--scan-only', action='store_true', help='Scan projects and exit without running web server')
    args = parser.parse_args()
    
    # Check if config file exists
    config_path = Path(args.config)
    if not config_path.exists():
        logger.error(f"Configuration file not found: {config_path}")
        sys.exit(1)
    
    # Load configuration
    with open(config_path, 'r') as config_file:
        config = yaml.safe_load(config_file)
    
    # Create absolute config path
    abs_config_path = os.path.abspath(config_path)
    
    if args.scan_only:
        # Run scanner only
        logger.info("Running project scan...")
        from project_scanner import ProjectScanner
        scanner = ProjectScanner(abs_config_path)
        projects = scanner.scan_directory()
        
        print("\nProject Scan Results:")
        print(f"Found {len(projects)} projects\n")
        
        for project in projects:
            print(f"- {project.name} ({project.status})")
            print(f"  Path: {project.path}")
            if project.is_git_repo:
                print(f"  Last commit: {project.last_commit_date}")
                print(f"  Commit frequency: {project.commit_frequency:.2f} per week")
            print("")
        
        sys.exit(0)
    
    # Create and run Flask app
    app = create_app(abs_config_path)
    
    host = config['web']['host']
    port = config['web']['port']
    debug = config['web']['debug']
    
    logger.info(f"Starting web server at http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    main() 