# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Deleting field 'LogAction.id'
        db.delete_column('object_log_logaction', 'id')

        # Adding field 'LogAction.template'
        db.add_column('object_log_logaction', 'template', self.gf('django.db.models.fields.CharField')(default='404.html', unique=True, max_length=128), keep_default=False)

        # Changing field 'LogAction.name'
        db.alter_column('object_log_logaction', 'name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=128, primary_key=True))

        # Deleting field 'LogItem.object_repr'
        db.delete_column('object_log_logitem', 'object_repr')

        # Deleting field 'LogItem.object_type'
        db.delete_column('object_log_logitem', 'object_type_id')

        # Deleting field 'LogItem.object_id'
        db.delete_column('object_log_logitem', 'object_id')

        # Deleting field 'LogItem.log_message'
        db.delete_column('object_log_logitem', 'log_message')

        # Adding field 'LogItem.object_id3'
        db.add_column('object_log_logitem', 'object_id3', self.gf('django.db.models.fields.PositiveIntegerField')(null=True), keep_default=False)

        # Adding field 'LogItem.object_id2'
        db.add_column('object_log_logitem', 'object_id2', self.gf('django.db.models.fields.PositiveIntegerField')(null=True), keep_default=False)

        # Adding field 'LogItem.object_id1'
        db.add_column('object_log_logitem', 'object_id1', self.gf('django.db.models.fields.PositiveIntegerField')(null=True), keep_default=False)

        # Adding field 'LogItem.object_type1'
        db.add_column('object_log_logitem', 'object_type1', self.gf('django.db.models.fields.related.ForeignKey')(related_name='log_items1', null=True, to=orm['contenttypes.ContentType']), keep_default=False)

        # Adding field 'LogItem.object_type2'
        db.add_column('object_log_logitem', 'object_type2', self.gf('django.db.models.fields.related.ForeignKey')(related_name='log_items2', null=True, to=orm['contenttypes.ContentType']), keep_default=False)

        # Adding field 'LogItem.object_type3'
        db.add_column('object_log_logitem', 'object_type3', self.gf('django.db.models.fields.related.ForeignKey')(related_name='log_items3', null=True, to=orm['contenttypes.ContentType']), keep_default=False)
    
    
    def backwards(self, orm):
        
        # Adding field 'LogAction.id'
        db.add_column('object_log_logaction', 'id', self.gf('django.db.models.fields.AutoField')(default=1, primary_key=True), keep_default=False)

        # Deleting field 'LogAction.template'
        db.delete_column('object_log_logaction', 'template')

        # Changing field 'LogAction.name'
        db.alter_column('object_log_logaction', 'name', self.gf('django.db.models.fields.CharField')(max_length=128, unique=True))

        # Adding field 'LogItem.object_repr'
        db.add_column('object_log_logitem', 'object_repr', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True), keep_default=False)

        # Adding field 'LogItem.object_type'
        db.add_column('object_log_logitem', 'object_type', self.gf('django.db.models.fields.related.ForeignKey')(default=1, related_name='log_items', to=orm['contenttypes.ContentType']), keep_default=False)

        # Adding field 'LogItem.object_id'
        db.add_column('object_log_logitem', 'object_id', self.gf('django.db.models.fields.PositiveIntegerField')(default=1), keep_default=False)

        # Adding field 'LogItem.log_message'
        db.add_column('object_log_logitem', 'log_message', self.gf('django.db.models.fields.TextField')(null=True, blank=True), keep_default=False)

        # Deleting field 'LogItem.object_id3'
        db.delete_column('object_log_logitem', 'object_id3')

        # Deleting field 'LogItem.object_id2'
        db.delete_column('object_log_logitem', 'object_id2')

        # Deleting field 'LogItem.object_id1'
        db.delete_column('object_log_logitem', 'object_id1')

        # Deleting field 'LogItem.object_type1'
        db.delete_column('object_log_logitem', 'object_type1_id')

        # Deleting field 'LogItem.object_type2'
        db.delete_column('object_log_logitem', 'object_type2_id')

        # Deleting field 'LogItem.object_type3'
        db.delete_column('object_log_logitem', 'object_type3_id')
    
    
    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
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
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'object_log.logaction': {
            'Meta': {'object_name': 'LogAction'},
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128', 'primary_key': 'True'}),
            'template': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'})
        },
        'object_log.logitem': {
            'Meta': {'object_name': 'LogItem'},
            'action': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['object_log.LogAction']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id1': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'object_id2': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'object_id3': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'object_type1': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'log_items1'", 'null': 'True', 'to': "orm['contenttypes.ContentType']"}),
            'object_type2': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'log_items2'", 'null': 'True', 'to': "orm['contenttypes.ContentType']"}),
            'object_type3': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'log_items3'", 'null': 'True', 'to': "orm['contenttypes.ContentType']"}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'log_items'", 'to': "orm['auth.User']"})
        }
    }
    
    complete_apps = ['object_log']
