from django.dispatch import Signal

pigeonpost_queue = Signal(providing_args=['render_email_method', 'scheduled_for', 'defer_for'])

pigeonpost_pre_send = Signal()

pigeonpost_post_send = Signal(providing_args=['successful'])
