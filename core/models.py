from django.db import models
import uuid
from uuid6 import uuid7

def generate_uuid7():
	"""Generate a UUID v7"""
	return uuid7()

class Profile(models.Model):
	id = models.UUIDField(primary_key=True, default=generate_uuid7, editable=False)
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
