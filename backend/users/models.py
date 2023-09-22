from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Переопределенная модель пользователя для создания обязательных полей"""

    email = models.EmailField(
        'электронная почта',
        max_length=150,
        unique=True,
        blank=False,
    )
    first_name = models.CharField(
        'имя',
        max_length=150,
        blank=False,
        null=False,
    )
    last_name = models.CharField(
        'фамилия',
        max_length=150,
        blank=False,
        null=False,
    )
    username = models.CharField('пользователь', max_length=150, unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'username']

    def __str__(self) -> str:
        return self.username

    class Meta:
        ordering = ['id']
        verbose_name = 'пользователь'
        verbose_name_plural = 'пользователи'


class UserSubscription(models.Model):
    """Модель подписок пользователей друг на друга."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followee',
        verbose_name='автор',
    )

    class Meta:
        ordering = ['-id']
        verbose_name = 'подписка'
        verbose_name_plural = 'подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'], name='unique_subscription',
            ),
        ]

    def __str__(self) -> str:
        return f'{self.user} оформил подписку на {self.author}.'
