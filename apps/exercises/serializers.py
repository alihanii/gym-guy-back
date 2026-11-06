from rest_framework import serializers

from .models import ExerciseTemplate


class ExerciseSerializer(serializers.ModelSerializer):
    thumbnail_url = serializers.SerializerMethodField()
    image_end_url = serializers.SerializerMethodField()

    class Meta:
        model = ExerciseTemplate
        fields = [
            "id", "slug", "title_en", "title_fa", "persian_aliases", "equipment", "tracking_type",
            "primary_muscle", "secondary_muscles", "injury_warnings", "thumbnail", "thumbnail_url",
            "image_end_url", "instructions", "level", "category", "source", "video", "is_custom", "listed",
        ]
        read_only_fields = ["id", "is_custom", "thumbnail_url", "image_end_url", "source", "listed"]
        extra_kwargs = {
            "slug": {"required": False},
            "thumbnail": {"write_only": True, "required": False},
            "video": {"required": False},
        }

    def get_thumbnail_url(self, obj):
        return self._url(obj.thumbnail)

    def get_image_end_url(self, obj):
        return self._url(obj.image_end)

    def _url(self, f):
        if not f:
            return None
        request = self.context.get("request")
        url = f.url
        return request.build_absolute_uri(url) if request and url.startswith("/") else url
