"""
Template tags for handling media files
"""
from django import template
from django.conf import settings
import os

register = template.Library()


@register.filter
def media_exists(media_file):
    """
    Check if a media file exists on the filesystem
    Usage: {% if project.banner|media_exists %}
    """
    if not media_file:
        return False
    
    try:
        file_path = os.path.join(settings.MEDIA_ROOT, str(media_file))
        return os.path.exists(file_path) and os.path.isfile(file_path)
    except Exception:
        return False


@register.simple_tag
def media_url_safe(media_file, fallback=''):
    """
    Get media URL with fallback for missing files
    Usage: {% media_url_safe project.banner %}
    """
    if not media_file:
        return fallback
    
    try:
        file_path = os.path.join(settings.MEDIA_ROOT, str(media_file))
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return media_file.url
        else:
            return fallback
    except Exception:
        return fallback


@register.inclusion_tag('media_image.html')
def safe_media_image(media_file, alt_text='', css_class='', fallback_text=''):
    """
    Render a media image with fallback for missing files
    Usage: {% safe_media_image project.banner project.name "img-fluid" %}
    """
    context = {
        'media_file': media_file,
        'alt_text': alt_text,
        'css_class': css_class,
        'fallback_text': fallback_text or (alt_text[:1].upper() if alt_text else '?'),
        'file_exists': media_exists(media_file) if media_file else False,
    }
    return context


@register.inclusion_tag('user_avatar.html')
def user_avatar(user, size='40', css_class=''):
    """
    Render user avatar with fallback to initials
    Usage: {% user_avatar user 60 "rounded-circle" %}
    """
    profile = getattr(user, 'userprofile', None)
    avatar = profile.avatar if profile else None

    # Generate fallback text (first letter of first name or username)
    if user.first_name:
        fallback_text = user.first_name[0].upper()
    else:
        fallback_text = user.username[0].upper()

    context = {
        'user': user,
        'avatar': avatar,
        'size': size,
        'css_class': css_class,
        'fallback_text': fallback_text,
        'alt_text': user.get_full_name() or user.username,
        'file_exists': media_exists(avatar) if avatar else False,
    }
    return context
