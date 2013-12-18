from django.contrib import admin
from django.core.urlresolvers import reverse

from django.contrib.admin import ModelAdmin
from pigeonpost.models import Pigeon, Outbox

class PigeonAdmin(ModelAdmin):
    list_display = ('id', 'source_content_type', 'source_edit', 'scheduled_for',
            'render_email_method', '_send_to', '_send_to_method', 'to_send', 'sent_at')
    list_filter = ('to_send',)

    related_lookup_fields = {
        'generic': [['source_content_type', 'source_id'], ],
    }

    def _send_to(self, obj):
        if obj.send_to:
            return obj.send_to
        return ''
    _send_to.short_description = 'send_to'

    def _send_to_method(self, obj):
        if obj.send_to_method:
            return obj.send_to_method
        return ''
    _send_to_method.short_description = 'send_to_method'

    def source_edit(self, obj):
        ct = obj.source_content_type
        if obj.source_id:
            url = reverse('admin:%s_%s_change' % (ct.app_label, ct.model), args=(obj.source_id,))
            return '<a href="%s">%s</a>' % (url,obj.source,)
        return '' # This must be a model class level pigeon
    source_edit.allow_tags = True

admin.site.register(Pigeon, PigeonAdmin)


class OutboxAdmin(ModelAdmin):
    list_display = ('id', 'user', 'pigeon_link', 'sent_at', 'succeeded', 'failures')
    list_filter = ('user',)

    def pigeon_link(self, obj):
        url = reverse('admin:pigeonpost_pigeon_change', args=(obj.pigeon.id,))
        return '<a href="%s">%s</a>' % (url,obj.pigeon.id,)
    pigeon_link.allow_tags = True

admin.site.register(Outbox, OutboxAdmin)

