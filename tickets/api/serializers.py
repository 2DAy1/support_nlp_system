from rest_framework import serializers


class TicketCreateRequestSerializer(serializers.Serializer):
    source = serializers.CharField(required=False, allow_blank=True)
    external_id = serializers.CharField(required=False, allow_blank=True)
    author_name = serializers.CharField(required=False, allow_blank=True)
    author_email = serializers.EmailField(required=False, allow_blank=True)
    rating = serializers.IntegerField(required=False, min_value=1, max_value=5)
    title = serializers.CharField()
    text = serializers.CharField()


class TicketCreateResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    company = serializers.CharField()
    source = serializers.CharField(allow_null=True)
    title = serializers.CharField()
    category = serializers.CharField(allow_null=True)
    department = serializers.CharField(allow_null=True)
    status = serializers.CharField()
    confidence = serializers.FloatField()


class ClassifyRequestSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, allow_blank=True)
    text = serializers.CharField(required=False, allow_blank=True)


class ClassifyResponseSerializer(serializers.Serializer):
    predicted_category = serializers.CharField()
    confidence = serializers.FloatField()
