from django.db import migrations


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
    ]
