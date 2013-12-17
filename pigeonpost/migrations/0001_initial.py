# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Pigeon'
        db.create_table('pigeonpost_pigeon', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('source_content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('source_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('successes', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('failures', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('to_send', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('sent_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('send_to', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
            ('send_to_method', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('render_email_method', self.gf('django.db.models.fields.TextField')(default='render_email')),
            ('scheduled_for', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal('pigeonpost', ['Pigeon'])

        # Adding model 'Outbox'
        db.create_table('pigeonpost_outbox', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('pigeon', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['pigeonpost.Pigeon'], null=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('message', self.gf('django.db.models.fields.TextField')()),
            ('sent_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('succeeded', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('failures', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('pigeonpost', ['Outbox'])

        # Adding unique constraint on 'Outbox', fields ['pigeon', 'user']
        db.create_unique('pigeonpost_outbox', ['pigeon_id', 'user_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'Outbox', fields ['pigeon', 'user']
        db.delete_unique('pigeonpost_outbox', ['pigeon_id', 'user_id'])

        # Deleting model 'Pigeon'
        db.delete_table('pigeonpost_pigeon')

        # Deleting model 'Outbox'
        db.delete_table('pigeonpost_outbox')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'pigeonpost.outbox': {
            'Meta': {'ordering': "['sent_at']", 'unique_together': "(('pigeon', 'user'),)", 'object_name': 'Outbox'},
            'failures': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'pigeon': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['pigeonpost.Pigeon']", 'null': 'True', 'blank': 'True'}),
            'sent_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'succeeded': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'pigeonpost.pigeon': {
            'Meta': {'ordering': "['scheduled_for']", 'object_name': 'Pigeon'},
            'failures': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'render_email_method': ('django.db.models.fields.TextField', [], {'default': "'render_email'"}),
            'scheduled_for': ('django.db.models.fields.DateTimeField', [], {}),
            'send_to': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'send_to_method': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'sent_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'source_content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'source_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'successes': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'to_send': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        }
    }

    complete_apps = ['pigeonpost']