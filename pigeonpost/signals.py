from django.dispatch import Signal

pigeonpost_signal = Signal(providing_args=['render_email_method', 'scheduled_for', 'defer_for'])
