# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models
from object_permissions.migrations import db_table_exists

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'TestModel'
        if not db_table_exists('object_permissions_testmodel'):
            db.create_table('object_permissions_testmodel', (
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                ('name', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ))
            db.send_create_signal('object_permissions', ['TestModel'])

        # Adding model 'TestModelChild'
        if not db_table_exists('object_permissions_testmodelchild'):
            db.create_table('object_permissions_testmodelchild', (
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['object_permissions.TestModel'], null=True)),
            ))
            db.send_create_signal('object_permissions', ['TestModelChild'])

        # Adding model 'TestModelChildChild'
        if not db_table_exists('object_permissions_testmodelchildchild'):
            db.create_table('object_permissions_testmodelchildchild', (
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['object_permissions.TestModelChild'], null=True)),
            ))
            db.send_create_signal('object_permissions', ['TestModelChildChild'])

        # Adding model 'TestModel_Perms'
        if not db_table_exists('object_permissions_testmodel_perms'):
            db.create_table('object_permissions_testmodel_perms', (
                ('obj', self.gf('django.db.models.fields.related.ForeignKey')(related_name='operms', to=orm['object_permissions.TestModel'])),
                ('Perm3', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
                ('Perm2', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
                ('Perm1', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
                ('Perm4', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
                ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='TestModel_uperms', null=True, to=orm['auth.User'])),
                ('group', self.gf('django.db.models.fields.related.ForeignKey')(related_name='TestModel_gperms', null=True, to=orm['auth.Group'])),
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ))
            db.send_create_signal('object_permissions', ['TestModel_Perms'])

        # Adding model 'TestModelChild_Perms'
        if not db_table_exists('object_permissions_testmodelchild_perms'):
            db.create_table('object_permissions_testmodelchild_perms', (
                ('obj', self.gf('django.db.models.fields.related.ForeignKey')(related_name='operms', to=orm['object_permissions.TestModelChild'])),
                ('Perm3', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
                ('Perm2', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
                ('Perm1', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
                ('Perm4', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
                ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='TestModelChild_uperms', null=True, to=orm['auth.User'])),
                ('group', self.gf('django.db.models.fields.related.ForeignKey')(related_name='TestModelChild_gperms', null=True, to=orm['auth.Group'])),
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ))
            db.send_create_signal('object_permissions', ['TestModelChild_Perms'])

        # Adding model 'TestModelChildChild_Perms'
        if not db_table_exists('object_permissions_testmodelchildchild_perms'):
            db.create_table('object_permissions_testmodelchildchild_perms', (
                ('obj', self.gf('django.db.models.fields.related.ForeignKey')(related_name='operms', to=orm['object_permissions.TestModelChildChild'])),
                ('Perm3', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
                ('Perm2', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
                ('Perm1', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
                ('Perm4', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
                ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='TestModelChildChild_uperms', null=True, to=orm['auth.User'])),
                ('group', self.gf('django.db.models.fields.related.ForeignKey')(related_name='TestModelChildChild_gperms', null=True, to=orm['auth.Group'])),
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ))
            db.send_create_signal('object_permissions', ['TestModelChildChild_Perms'])

        # Adding model 'Group_Perms'
        if not db_table_exists('object_permissions_group_perms'):
            db.create_table('object_permissions_group_perms', (
                ('admin', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
                ('obj', self.gf('django.db.models.fields.related.ForeignKey')(related_name='operms', to=orm['auth.Group'])),
                ('group', self.gf('django.db.models.fields.related.ForeignKey')(related_name='Group_gperms', null=True, to=orm['auth.Group'])),
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='Group_uperms', null=True, to=orm['auth.User'])),
            ))
            db.send_create_signal('object_permissions', ['Group_Perms'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'TestModel'
        db.delete_table('object_permissions_testmodel')

        # Deleting model 'TestModelChild'
        db.delete_table('object_permissions_testmodelchild')

        # Deleting model 'TestModelChildChild'
        db.delete_table('object_permissions_testmodelchildchild')

        # Deleting model 'TestModel_Perms'
        db.delete_table('object_permissions_testmodel_perms')

        # Deleting model 'TestModelChild_Perms'
        db.delete_table('object_permissions_testmodelchild_perms')

        # Deleting model 'TestModelChildChild_Perms'
        db.delete_table('object_permissions_testmodelchildchild_perms')

        # Deleting model 'Group_Perms'
        db.delete_table('object_permissions_group_perms')
    
    
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
            'admin': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
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
            'Perm1': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'Perm2': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'Perm3': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'Perm4': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
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
            'Perm1': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'Perm2': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'Perm3': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'Perm4': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
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
            'Perm1': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'Perm2': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'Perm3': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'Perm4': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'TestModelChildChild_gperms'", 'null': 'True', 'to': "orm['auth.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'obj': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'operms'", 'to': "orm['object_permissions.TestModelChildChild']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'TestModelChildChild_uperms'", 'null': 'True', 'to': "orm['auth.User']"})
        },
    }
    
    complete_apps = ['object_permissions']
