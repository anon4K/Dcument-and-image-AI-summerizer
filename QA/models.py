from django.db import models

class QueryLog(models.Model):
    filename = models.CharField(max_length=255, blank=True)
    file_kind = models.CharField(max_length=20, blank=True)  # "image" or "document"
    question = models.TextField()
    answer = models.TextField(blank=True)
    input_tokens = models.IntegerField(default=0)
    output_tokens = models.IntegerField(default=0)
    latency_ms = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    