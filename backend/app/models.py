import uuid
from django.db import models


class Member(models.Model):
    # 会員番号：8桁数字想定（API側でもバリデーション）
    member_number = models.CharField(max_length=8, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.member_number}:{self.name}"


class CallSession(models.Model):
    class State(models.TextChoices):
        ASK_MEMBER = "ASK_MEMBER"
        ASK_ORDER = "ASK_ORDER"
        COMPLETED = "COMPLETED"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    state = models.CharField(
        max_length=16,
        choices=State.choices,
        default=State.ASK_MEMBER,
    )

    # 会員確定前はnull
    member = models.ForeignKey(Member, null=True, blank=True, on_delete=models.SET_NULL)

    # 直近エラー（フロントで表示しやすく）
    last_error_code = models.CharField(max_length=64, null=True, blank=True)
    last_error_message = models.CharField(max_length=255, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Order(models.Model):
    # 冪等性：1セッション=1注文（同じsessionで2重登録しない）
    session = models.OneToOneField(CallSession, on_delete=models.CASCADE, related_name="order")
    member = models.ForeignKey(Member, on_delete=models.PROTECT)

    order_number = models.CharField(max_length=8)
    quantity = models.PositiveIntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["order_number"]),
        ]
