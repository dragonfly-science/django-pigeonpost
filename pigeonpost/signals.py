from django.dispatch import Signal

pigeonpost_queue = Signal(providing_args=['render_email_method', 'scheduled_for', 'defer_for', 'retry'])

pigeonpost_pre_send = Signal()

pigeonpost_post_send = Signal(providing_args=['successful'])

# Ensure that signal listeners are processed
import pigeonpost.tasks

