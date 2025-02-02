from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core_api", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Thread",
            fields=[
                (
                    "thread_id",
                    models.CharField(max_length=255, primary_key=True, serialize=False),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
