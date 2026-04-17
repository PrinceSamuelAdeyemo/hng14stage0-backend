from django.db import models
import uuid

def generate_uuid_v7():
	"""Generate a UUID v7 if available, otherwise UUID v4"""
	try:
		from uuid6 import uuid7
		return uuid7()
	except (ImportError, Exception):
		# Fallback to UUID v4 if uuid6 is not available
		return uuid.uuid4()

class Profile(models.Model):
	id = models.UUIDField(primary_key=True, default=generate_uuid_v7, editable=False)
	name = models.CharField(max_length=100, unique=True)
	gender = models.CharField(max_length=20)
	gender_probability = models.FloatField()
	sample_size = models.IntegerField()
	age = models.IntegerField()
	age_group = models.CharField(max_length=20)
	country_id = models.CharField(max_length=10)
	country_probability = models.FloatField()
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.name
