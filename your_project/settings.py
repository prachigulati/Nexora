"""
Django settings for your_project.

This file imports all settings from the actual app.settings module.
This is a workaround for Render deployment that expects 'your_project' as the project name.
"""

# Import all settings from the actual app settings
from app.settings import *
