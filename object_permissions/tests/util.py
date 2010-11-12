def install_model(model):
    from django.core.management import sql, color
    from django import db
    from django.db import connection

    # Standard syncdb expects models to be in reliable locations,
    # so dynamic models need to bypass django.core.management.syncdb.
    # On the plus side, this allows individual models to be installed
    # without installing the entire project structure.
    # On the other hand, this means that things like relationships and
    # indexes will have to be handled manually.
    # This installs only the basic table definition.

    # disable terminal colors in the sql statements
    style = color.no_style()

    cursor = connection.cursor()
    statements, related = connection.creation.sql_create_model(model, style)
    for sql in statements:
        try:
            cursor.execute(sql)
        except db.utils.DatabaseError:
            pass