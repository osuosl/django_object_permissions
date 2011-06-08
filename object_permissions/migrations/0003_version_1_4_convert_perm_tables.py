# encoding: utf-8
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def convert_table(self, table, perms):
        for row in table.objects.all():
            for perm in perms:
                row.__dict__[perm] = row.__dict__['%s_tmp'%perm]
            row.save()

    def revert_table(self, table, perms):
        for row in table.objects.all():
            for perm in perms:
                row.__dict__['%s_tmp'%perm] = row.__dict__[perm]
            row.save()

    def forwards(self, orm):
        self.convert_table(orm['object_permissions.group_perms'], ['admin'])
    
    def backwards(self, orm):
        self.revert_table(orm['object_permissions.group_perms'], ['admin'])
    
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
        'object_permissions.group_perms': {
            'Meta': {'object_name': 'Group_Perms'},
            'admin': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'admin_tmp': ('django.db.models.fields.IntegerField', [], {'default': 'False'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Group_gperms'", 'null': 'True', 'to': "orm['auth.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'obj': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'operms'", 'to': "orm['auth.Group']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Group_uperms'", 'null': 'True', 'to': "orm['auth.User']"})
        },
        'object_permissions.testmodel': {
            'Meta': {'object_name': 'TestModel'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '32'})
        },
        'object_permissions.testmodel_perms': {
            'Meta': {'object_name': 'TestModel_Perms'},
            'Perm1': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'Perm2': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'Perm3': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'Perm4': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'TestModel_gperms'", 'null': 'True', 'to': "orm['auth.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'obj': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'operms'", 'to': "orm['object_permissions.TestModel']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'TestModel_uperms'", 'null': 'True', 'to': "orm['auth.User']"})
        },
        'object_permissions.testmodelchild': {
            'Meta': {'object_name': 'TestModelChild'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['object_permissions.TestModel']", 'null': 'True'})
        },
        'object_permissions.testmodelchild_perms': {
            'Meta': {'object_name': 'TestModelChild_Perms'},
            'Perm1': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'Perm2': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'Perm3': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'Perm4': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'TestModelChild_gperms'", 'null': 'True', 'to': "orm['auth.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'obj': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'operms'", 'to': "orm['object_permissions.TestModelChild']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'TestModelChild_uperms'", 'null': 'True', 'to': "orm['auth.User']"})
        },
        'object_permissions.testmodelchildchild': {
            'Meta': {'object_name': 'TestModelChildChild'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['object_permissions.TestModelChild']", 'null': 'True'})
        },
        'object_permissions.testmodelchildchild_perms': {
            'Meta': {'object_name': 'TestModelChildChild_Perms'},
            'Perm1': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'Perm2': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'Perm3': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'Perm4': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'TestModelChildChild_gperms'", 'null': 'True', 'to': "orm['auth.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'obj': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'operms'", 'to': "orm['object_permissions.TestModelChildChild']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'TestModelChildChild_uperms'", 'null': 'True', 'to': "orm['auth.User']"})
        }
    }
    
    complete_apps = ['object_permissions']
