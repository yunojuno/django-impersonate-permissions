{% load humanize %} You are currently impersonating {{ impersonating.get_full_name }}. Your session will expire at {{ window.window_ends_at | naturaltime }} ({{ window.window_ends_at }}).
