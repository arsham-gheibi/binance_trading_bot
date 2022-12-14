# Generated by Django 4.1.2 on 2022-10-11 11:31

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('api_key', models.CharField(max_length=100, unique=True)),
                ('api_secret', models.CharField(max_length=100, unique=True)),
                ('telegram_id', models.BigIntegerField(unique=True)),
                ('user_name', models.CharField(max_length=100, unique=True)),
                ('balance', models.FloatField(null=True)),
                ('usage_percentage', models.FloatField(default=2.0)),
                ('is_active', models.BooleanField(default=True)),
                ('date_added', models.DateTimeField(auto_now_add=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
            ],
            options={
                'ordering': ('-date_added',),
            },
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.UUIDField(editable=False, primary_key=True, serialize=False, unique=True)),
                ('changed_stop', models.BooleanField(default=False)),
                ('type', models.CharField(max_length=255)),
                ('qty', models.FloatField()),
                ('is_cancelled', models.BooleanField(default=False)),
                ('is_closed', models.BooleanField(default=False)),
                ('date_added', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ('-date_added',),
            },
        ),
        migrations.CreateModel(
            name='Precision',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('symbol', models.CharField(max_length=40)),
                ('tick_size', models.IntegerField(null=True)),
                ('max_trading_qty', models.FloatField(null=True)),
                ('min_trading_qty', models.FloatField(null=True)),
                ('qty_step', models.IntegerField(null=True)),
                ('date_added', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ('-date_added',),
            },
        ),
        migrations.CreateModel(
            name='Queue',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20)),
                ('is_available', models.BooleanField(default=True)),
                ('is_main', models.BooleanField(default=False, editable=False)),
                ('is_stream', models.BooleanField(default=False, editable=False)),
                ('is_notifier', models.BooleanField(default=False, editable=False)),
                ('date_added', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ('-date_added',),
            },
        ),
        migrations.CreateModel(
            name='Signal',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('message_text', models.TextField(editable=False, unique=True)),
                ('symbol', models.CharField(max_length=50)),
                ('order_type', models.CharField(max_length=50)),
                ('side', models.CharField(max_length=50)),
                ('time_frame', models.CharField(max_length=50)),
                ('strategy', models.CharField(max_length=50)),
                ('entry', models.FloatField()),
                ('stop_loss', models.FloatField()),
                ('position_side', models.CharField(default='BOTH', max_length=50)),
                ('time_in_force', models.CharField(default='GTC', max_length=50)),
                ('reduce_only', models.BooleanField(default=False)),
                ('stopped', models.BooleanField(default=False)),
                ('date_added', models.DateTimeField(auto_now_add=True)),
                ('precision', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.precision')),
            ],
            options={
                'ordering': ('-date_added',),
            },
        ),
        migrations.CreateModel(
            name='Target',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('value', models.FloatField()),
                ('percent', models.FloatField()),
                ('num', models.IntegerField()),
                ('hit', models.BooleanField(default=False)),
                ('side', models.CharField(max_length=50)),
                ('date_added', models.DateTimeField(auto_now_add=True)),
                ('signal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.signal')),
            ],
            options={
                'ordering': ('num',),
            },
        ),
        migrations.CreateModel(
            name='TargetOrder',
            fields=[
                ('id', models.UUIDField(editable=False, primary_key=True, serialize=False, unique=True)),
                ('date_added', models.DateTimeField(auto_now_add=True)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.order')),
                ('target', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.target')),
            ],
            options={
                'ordering': ('-date_added',),
            },
        ),
        migrations.AddField(
            model_name='order',
            name='signal',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.signal'),
        ),
        migrations.AddField(
            model_name='order',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='user',
            name='main_queue',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='main_queue', to='core.queue'),
        ),
        migrations.AddField(
            model_name='user',
            name='notifier_queue',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='notifier_queue', to='core.queue'),
        ),
        migrations.AddField(
            model_name='user',
            name='stream_queue',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='stream_queue', to='core.queue'),
        ),
        migrations.AddField(
            model_name='user',
            name='user_permissions',
            field=models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions'),
        ),
    ]
