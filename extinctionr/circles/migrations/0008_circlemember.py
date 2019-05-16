# Generated by Django 2.2 on 2019-05-16 20:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('circles', '0007_auto_20190503_1316'),
    ]

    operations = [
        migrations.CreateModel(
            name='CircleMember',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(max_length=255)),
                ('join_date', models.DateTimeField(auto_now_add=True)),
                ('circle', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='circles.Circle')),
                ('contact', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contacts.Contact')),
            ],
            options={
                'unique_together': {('circle', 'contact', 'role')},
            },
        ),
    ]
