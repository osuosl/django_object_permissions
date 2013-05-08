from django.db import models

from object_permissions import register


class TestModel(models.Model):
    name = models.CharField(max_length=32)


class TestModelChild(models.Model):
    parent = models.ForeignKey(TestModel, null=True)


class TestModelChildChild(models.Model):
    parent = models.ForeignKey(TestModelChild, null=True)


TEST_MODEL_PARAMS = {
    'perms': {
        # perm with both params
        'Perm1': {
            'description': 'The first permission',
            'label': 'Perm One'
        },
        # perm with only description
        'Perm2': {
            'description': 'The second permission',
        },
        # perm with only label
        'Perm3': {
            'label': 'Perm Three'
        },
        # perm with no params
        'Perm4': {}
    },
    'url': 'test_model-detail',
    'url-params': ['name']
}

register(
    TEST_MODEL_PARAMS,
    TestModel,
    'object_permissions'
)
register(
    ['Perm1', 'Perm2', 'Perm3', 'Perm4'],
    TestModelChild,
    'object_permissions'
)
register(
    ['Perm1', 'Perm2', 'Perm3', 'Perm4'],
    TestModelChildChild,
    'object_permissions'
)
