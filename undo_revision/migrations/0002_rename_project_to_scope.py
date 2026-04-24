from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    dependencies = [
        ("undo_revision", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="revision",
            old_name="project",
            new_name="scope",
        ),
        migrations.AlterField(
            model_name="version",
            name="object_id",
            field=models.TextField(),
        ),
    ]
