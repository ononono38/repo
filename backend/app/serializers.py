from rest_framework import serializers

class MemberLookupSerializer(serializers.Serializer):
    member_number = serializers.RegexField(
        regex=r"^\d{8}$",
        error_messages={"invalid": "組合員番号は8桁の数字で入力してください"},
    )

class OrderCreateSerializer(serializers.Serializer):
    order_number = serializers.RegexField(
        regex=r"^\d{8}$",
        error_messages={"invalid": "注文番号は8桁の数字で入力してください"},
    )
    quantity = serializers.IntegerField(min_value=1, required=False, default=1)
