"""
URL configuration for your_project.

This file imports all URLs from the actual app.urls module.
This is a workaround for Render deployment that expects 'your_project' as the project name.
"""

# Import all URLs from the actual app URLs
from app.urls import *
