"""
Routes for the Project Tracker Flask application.
"""
from flask import Blueprint, render_template, jsonify, request, current_app
import sys
import os
import logging
from datetime import datetime
import git
from git.exc import GitCommandError

# Add parent directory to path so we can import project_scanner
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from project_scanner import ProjectScanner

# Configure logging
logger = logging.getLogger('routes')

# Create Blueprint
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Render the main dashboard page."""
    return render_template('index.html')

@main_bp.route('/projects')
def get_projects():
    """API endpoint to get all projects as JSON."""
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.yaml')
        scanner = ProjectScanner(config_path)
        projects = scanner.scan_directory()
        
        # Convert datetime objects to strings for JSON serialization
        project_data = [p.to_dict() for p in projects]
        
        # Get filter parameters
        status_filter = request.args.get('status', None)
        sort_by = request.args.get('sort', 'name')
        
        # Apply filters
        if status_filter and status_filter != 'All':
            project_data = [p for p in project_data if p['status'] == status_filter]
        
        # Sort projects
        if sort_by == 'name':
            project_data.sort(key=lambda x: x['name'].lower())
        elif sort_by == 'status':
            project_data.sort(key=lambda x: x['status'])
        elif sort_by == 'last_commit':
            # Sort by last commit date (if available)
            def get_commit_date(project):
                if project['last_commit_date']:
                    return datetime.fromisoformat(project['last_commit_date'])
                return datetime.min
            project_data.sort(key=get_commit_date, reverse=True)
        
        # Check for alerts
        active_projects = [p for p in project_data if p['status'] == 'Active']
        alerts = []
        
        # Alert if there are too many active projects
        config = current_app.config['CONFIG']
        active_threshold = config['notifications'].get('active_projects_alert', 3)
        if len(active_projects) >= active_threshold:
            alerts.append({
                'type': 'warning',
                'message': f"You have {len(active_projects)} active projects. Consider focusing on completing existing projects before starting new ones."
            })
        
        return jsonify({
            'projects': project_data,
            'alerts': alerts,
            'counts': {
                'total': len(project_data),
                'active': len([p for p in project_data if p['status'] == 'Active']),
                'dormant': len([p for p in project_data if p['status'] == 'Dormant']),
                'inactive': len([p for p in project_data if p['status'] == 'Inactive']),
                'abandoned': len([p for p in project_data if p['status'] == 'Abandoned']),
                'unknown': len([p for p in project_data if p['status'] == 'Unknown'])
            }
        })
    except Exception as e:
        logger.error(f"Error getting projects: {str(e)}")
        return jsonify({'error': str(e)}), 500

@main_bp.route('/scan', methods=['POST'])
def scan_now():
    """Trigger a new scan of the projects directory."""
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.yaml')
        scanner = ProjectScanner(config_path)
        projects = scanner.scan_directory()
        return jsonify({'status': 'success', 'count': len(projects)})
    except Exception as e:
        logger.error(f"Error during scan: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@main_bp.route('/git/pull', methods=['POST'])
def git_pull():
    """Pull changes from remote repository."""
    try:
        data = request.get_json()
        repo_path = data.get('path')
        
        if not repo_path:
            return jsonify({'error': 'No repository path provided'}), 400
        
        repo = git.Repo(repo_path)
        origin = repo.remotes.origin
        origin.pull()
        
        return jsonify({'status': 'success', 'message': 'Successfully pulled changes'})
    except GitCommandError as e:
        logger.error(f"Git pull error: {str(e)}")
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        logger.error(f"Error during pull: {str(e)}")
        return jsonify({'error': str(e)}), 500

@main_bp.route('/git/commit', methods=['POST'])
def git_commit():
    """Commit changes in repository."""
    try:
        data = request.get_json()
        repo_path = data.get('path')
        message = data.get('message')
        
        if not repo_path or not message:
            return jsonify({'error': 'Repository path and commit message are required'}), 400
        
        repo = git.Repo(repo_path)
        repo.git.add(A=True)  # Stage all changes
        repo.index.commit(message)
        
        return jsonify({'status': 'success', 'message': 'Successfully committed changes'})
    except GitCommandError as e:
        logger.error(f"Git commit error: {str(e)}")
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        logger.error(f"Error during commit: {str(e)}")
        return jsonify({'error': str(e)}), 500

@main_bp.route('/git/push', methods=['POST'])
def git_push():
    """Push changes to remote repository."""
    try:
        data = request.get_json()
        repo_path = data.get('path')
        
        if not repo_path:
            return jsonify({'error': 'No repository path provided'}), 400
        
        repo = git.Repo(repo_path)
        origin = repo.remotes.origin
        origin.push()
        
        return jsonify({'status': 'success', 'message': 'Successfully pushed changes'})
    except GitCommandError as e:
        logger.error(f"Git push error: {str(e)}")
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        logger.error(f"Error during push: {str(e)}")
        return jsonify({'error': str(e)}), 500 