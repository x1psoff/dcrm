from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("website", "0070_alter_record_customer"),
    ]

    operations = [
        migrations.CreateModel(
            name="TailscaleInviteLink",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("url", models.URLField(unique=True, verbose_name="Ссылка приглашения")),
                ("used_at", models.DateTimeField(blank=True, null=True, verbose_name="Когда использована")),
                (
                    "used_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="tailscale_invites_used",
                        to="auth.user",
                        verbose_name="Кому выдана (user)",
                    ),
                ),
            ],
            options={
                "verbose_name": "Tailscale invite link",
                "verbose_name_plural": "Tailscale invite links",
                "ordering": ["id"],
            },
        ),
    ]


