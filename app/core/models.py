from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.db import models
from django.conf import settings
import uuid


class UserManager(BaseUserManager):
    def create_user(
        self,
        api_key,
        api_secret,
        telegram_id,
        user_name,
        usage_percentage=2.0,
        password=None
    ):

        user = self.model(
            api_key=api_key,
            api_secret=api_secret,
            telegram_id=telegram_id,
            user_name=user_name,
            usage_percentage=usage_percentage
        )

        user.set_password(password)
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    api_key = models.CharField(max_length=100, unique=True)
    api_secret = models.CharField(max_length=100, unique=True)
    telegram_id = models.BigIntegerField(unique=True)
    user_name = models.CharField(max_length=100, unique=True)
    balance = models.FloatField(null=True)
    usage_percentage = models.FloatField(default=2.0)
    bot_token = models.CharField(max_length=255, null=True)
    main_queue = models.OneToOneField(
        'Queue', models.SET_NULL, related_name=_('main_queue'), null=True)
    stream_queue = models.OneToOneField(
        'Queue', models.SET_NULL, related_name=_('stream_queue'), null=True)
    notifier_queue = models.OneToOneField(
        'Queue', models.SET_NULL, related_name=_('notifier_queue'), null=True)
    is_active = models.BooleanField(default=True)
    date_added = models.DateTimeField(auto_now_add=True)
    objects = UserManager()
    USERNAME_FIELD = 'api_key'

    class Meta:
        ordering = ('-date_added',)

    def __str__(self):
        return self.user_name


class Queue(models.Model):
    name = models.CharField(max_length=20)
    is_available = models.BooleanField(default=True)
    is_main = models.BooleanField(default=False, editable=False)
    is_stream = models.BooleanField(default=False, editable=False)
    is_notifier = models.BooleanField(default=False, editable=False)
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-date_added',)

    def __str__(self):
        return f'#{self.name} {self.is_available}'


class Inspector(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.CASCADE)
    code = models.CharField(max_length=255)
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-date_added',)

    def __str__(self):
        return f'{self.user.user_name} {self.code}'


class Target(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    signal = models.ForeignKey('Signal', models.CASCADE)
    value = models.FloatField()
    percent = models.FloatField()
    num = models.IntegerField()
    hit = models.BooleanField(default=False)
    side = models.CharField(max_length=50)
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('num',)

    def __str__(self):
        return f'#{self.signal.symbol} {self.num} {self.hit}'


class Signal(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    precision = models.ForeignKey('Precision', models.SET_NULL, null=True)
    message_text = models.TextField(editable=False, unique=True)
    symbol = models.CharField(max_length=50)
    order_type = models.CharField(max_length=50)
    side = models.CharField(max_length=50)
    time_frame = models.CharField(max_length=50)
    strategy = models.CharField(max_length=50)
    entry = models.FloatField()
    stop_loss = models.FloatField()
    position_side = models.CharField(max_length=50, default='BOTH')
    time_in_force = models.CharField(max_length=50, default='GTC')
    reduce_only = models.BooleanField(default=False)
    stopped = models.BooleanField(default=False)
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-date_added',)

    def __str__(self):
        return f'#{self.symbol} {self.order_type}'


class Order(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.CASCADE)
    signal = models.ForeignKey('Signal', models.CASCADE)
    changed_stop = models.BooleanField(default=False)
    type = models.CharField(max_length=255)
    qty = models.FloatField()
    is_cancelled = models.BooleanField(default=False)
    is_closed = models.BooleanField(default=False)
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-date_added',)

    def __str__(self):
        return f'#{self.signal.symbol} {self.user.user_name} {self.qty}'


class TargetOrder(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, unique=True)
    order = models.ForeignKey('Order', models.CASCADE)
    target = models.ForeignKey('Target', models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-date_added',)

    def __str__(self):
        return f'#{self.target.signal.symbol} {self.target.num}'


class Precision(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    symbol = models.CharField(max_length=40)
    tick_size = models.IntegerField(null=True)
    max_trading_qty = models.FloatField(null=True)
    min_trading_qty = models.FloatField(null=True)
    qty_step = models.IntegerField(null=True)
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-date_added',)

    def __str__(self):
        return f'#{self.symbol} {self.tick_size} {self.qty_step}'
