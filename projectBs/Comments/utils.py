from django.utils.timesince import timesince
from datetime import datetime
from functools import wraps
from django.http import JsonResponse, HttpResponseNotAllowed, HttpResponseServerError
from django.db import connection
from rest_framework.authtoken.models import Token

def format_time_since(timestamp):
    if timestamp is None:
        return "null"
    
    now = datetime.now()
    delta = now - timestamp
    if delta.days > 0:
        return f"{delta.days} days ago"
    elif delta.seconds < 60:
        return f"{delta.seconds} seconds ago"
    elif delta.seconds < 3600:
        return f"{delta.seconds // 60} minutes ago"
    else:
        return f"{delta.seconds // 3600} hours ago"