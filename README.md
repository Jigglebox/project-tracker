# Project Tracker

A tool to help you monitor and manage your coding projects by scanning directories, analyzing git repositories, and providing a visual dashboard.

## Features

- **Automatic Project Discovery**: Scans directories recursively to find code projects based on common markers (like .git, README, package.json, etc.)
- **Git Analysis**: For git repositories, analyzes commit history to determine activity levels
- **Project Classification**: Automatically classifies projects as Active, Dormant, Inactive, or Abandoned based on commit frequency
- **Web Dashboard**: Provides an interactive web interface to browse, filter, and sort your projects
- **Notifications**: Alerts you when you have too many active projects, helping you focus on finishing what you've started

## Installation

### Prerequisites

- Python 3.7 or higher
- Git (for repository analysis)

### Setup

1. Clone or download this repository:
   ```
   git clone <repository-url>
   cd project-tracker
   ```

2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Configure the application:
   - Edit `config.yaml` to set your project root directory and other settings

## Usage

### Starting the Web Dashboard

Run the application with:

```
python main.py
```

Then open your browser and navigate to http://127.0.0.1:5000 (or the host/port you configured).

### Command-line Scan

To perform a quick scan without starting the web server:

```
python main.py --scan-only
```

### Configuration

Edit `config.yaml` to customize:

- **scan_directory**: Root directory to scan for projects
- **thresholds**: Time thresholds for classifying project activity (in days)
- **project_markers**: Files/directories that identify a code project
- **web**: Web server settings (host, port, debug mode)
- **notifications**: Configure alerts for too many active projects

Example configuration:

```yaml
# Directory to scan for code projects
scan_directory: "D:/Documents/Scripts"  # Change this to your code projects root directory

# Project classification thresholds (in days)
thresholds:
  active: 30       # Projects with commits in the last 30 days
  dormant: 90      # Projects with commits between 30 and 90 days ago
  abandoned: 180   # Projects with no commits for more than 180 days
```

## Dashboard Features

- **Project Overview**: At-a-glance statistics of your projects by status
- **Filtering**: Filter projects by status (Active, Dormant, Inactive, Abandoned)
- **Sorting**: Sort projects by name, status, or last commit date
- **Project Cards**: Each project displays key information like:
  - Project name and path
  - Creation and modification dates
  - Git repository details (when available)
  - Commit frequency and last commit date
- **Responsive Design**: Works on desktop and mobile devices

## Extending the Tool

The codebase is designed to be modular and extensible:

- **project_scanner.py**: Contains the core scanning and analysis logic
- **app/routes.py**: Handles web API endpoints
- **app/templates/index.html**: Main dashboard UI

To add new features, you might:
- Add new project classifications in `project_scanner.py`
- Enhance the dashboard with additional visualizations in the HTML/JavaScript
- Add new API endpoints in `routes.py`

## Troubleshooting

- **No projects found**: Check your `scan_directory` setting in config.yaml
- **Git analysis not working**: Ensure GitPython is properly installed and git is available on your system path
- **Web dashboard not starting**: Check for port conflicts in the web server configuration 