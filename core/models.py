from django.db import models
import uuid

# Use standard UUID v4 for Vercel compatibility
# TODO: Can upgrade to UUID v7 later with uuid6 package
def generate_uuid():
	"""Generate a UUID"""
	return uuid.uuid4()

class Profile(models.Model):
	id = models.UUIDField(primary_key=True, default=generate_uuid, editable=False)
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
