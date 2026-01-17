from django.db import transaction, IntegrityError
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.exceptions import NotFound

from app.models import CallSession, Member, Order
from app.serializers import MemberLookupSerializer, OrderCreateSerializer
from app.responses import ok, ng

PROMPT_ASK_MEMBER = "組合員番号を入力してください"
PROMPT_ASK_ORDER = "注文番号を入力してください"


class SessionCreateView(APIView):
    def post(self, request):
        s = CallSession.objects.create(state=CallSession.State.ASK_MEMBER)
        return ok(
            {
                "session_id": str(s.id),
                "state": s.state,
                "prompt": PROMPT_ASK_MEMBER,
            },
            status=status.HTTP_201_CREATED,
        )


class SessionRetrieveView(APIView):
    def get(self, request, session_id):
        try:
            s = CallSession.objects.select_related("member").get(id=session_id)
        except CallSession.DoesNotExist:
            raise NotFound("session not found")

        member = None
        if s.member:
            member = {"member_number": s.member.member_number, "name": s.member.name}

        last_error = None
        if s.last_error_code:
            last_error = {"code": s.last_error_code, "message": s.last_error_message}

        return ok(
            {
                "session_id": str(s.id),
                "state": s.state,
                "member": member,
                "last_error": last_error,
            }
        )


class MemberLookupView(APIView):
    def post(self, request, session_id):
        try:
            s = CallSession.objects.select_related("member").get(id=session_id)
        except CallSession.DoesNotExist:
            raise NotFound("session not found")

        # COMPLETEDは何もできない
        if s.state == CallSession.State.COMPLETED:
            return ng(
                state=s.state,
                code="ALREADY_COMPLETED",
                message="このセッションはすでに完了しています。",
                status=status.HTTP_409_CONFLICT,
            )

        # ASK_MEMBER以外で照会したら状態不整合
        if s.state != CallSession.State.ASK_MEMBER:
            return ng(
                state=s.state,
                code="INVALID_STATE",
                message="会員照会できる状態ではありません。",
                status=status.HTTP_409_CONFLICT,
            )

        ser = MemberLookupSerializer(data=request.data)
        if not ser.is_valid():
            return ng(
                state=s.state,
                code="VALIDATION_ERROR",
                message=ser.errors["member_number"][0],
                status=400,
                prompt=PROMPT_ASK_MEMBER,
            )

        member_number = ser.validated_data["member_number"]

        try:
            m = Member.objects.get(member_number=member_number, is_active=True)
        except Member.DoesNotExist:
            s.last_error_code = "MEMBER_NOT_FOUND"
            s.last_error_message = "組合員番号が見つかりません。もう一度入力してください。"
            s.save(update_fields=["last_error_code", "last_error_message", "updated_at"])
            return ng(
                state=s.state,
                code="MEMBER_NOT_FOUND",
                message=s.last_error_message,
                status=400,
                prompt=PROMPT_ASK_MEMBER,
            )

        # 成功：ASK_ORDERへ
        s.member = m
        s.state = CallSession.State.ASK_ORDER
        s.last_error_code = None
        s.last_error_message = None
        s.save()

        return ok(
            {
                "state": s.state,
                "member": {"member_number": m.member_number, "name": m.name},
                "prompt": f"{m.name}様ですね。{PROMPT_ASK_ORDER}",
            }
        )


class OrderCreateView(APIView):
    @transaction.atomic
    def post(self, request, session_id):
        try:
            s = CallSession.objects.select_for_update().select_related("member").get(id=session_id)
        except CallSession.DoesNotExist:
            raise NotFound("session not found")

        if s.state == CallSession.State.COMPLETED:
            return ng(
                state=s.state,
                code="ALREADY_COMPLETED",
                message="このセッションはすでに完了しています。",
                status=status.HTTP_409_CONFLICT,
            )

        if s.state != CallSession.State.ASK_ORDER:
            return ng(
                state=s.state,
                code="INVALID_STATE",
                message="注文登録できる状態ではありません。",
                status=status.HTTP_409_CONFLICT,
            )

        if s.member is None:
            return ng(state=s.state, code="NO_MEMBER", message="会員が確定していません。", status=409)

        ser = OrderCreateSerializer(data=request.data)
        if not ser.is_valid():
            # order_number or quantity
            msg = ser.errors.get("order_number", ser.errors.get("quantity"))[0]
            return ng(
                state=s.state,
                code="VALIDATION_ERROR",
                message=msg,
                status=400,
                prompt=PROMPT_ASK_ORDER,
            )

        order_number = ser.validated_data["order_number"]
        quantity = ser.validated_data["quantity"]

        # 例：簡易ルール（先頭0は不正）
        if order_number.startswith("0"):
            s.last_error_code = "INVALID_ORDER"
            s.last_error_message = "注文番号が不正です。もう一度入力してください。"
            s.save(update_fields=["last_error_code", "last_error_message", "updated_at"])
            return ng(
                state=s.state,
                code="INVALID_ORDER",
                message=s.last_error_message,
                status=400,
                prompt=PROMPT_ASK_ORDER,
            )

        # 冪等性（DB制約OneToOne + 例外処理）
        try:
            o = Order.objects.create(
                session=s,
                member=s.member,
                order_number=order_number,
                quantity=quantity,
            )
        except IntegrityError:
            return ng(
                state=s.state,
                code="DUPLICATE_ORDER",
                message="すでに注文登録済みです。",
                status=status.HTTP_409_CONFLICT,
            )

        s.state = CallSession.State.COMPLETED
        s.last_error_code = None
        s.last_error_message = None
        s.save()

        return ok(
            {
                "state": s.state,
                "order": {"order_number": o.order_number, "quantity": o.quantity},
                "thank_you_message": "ご注文ありがとうございました。配送手配を進めます。",
            }
        )
