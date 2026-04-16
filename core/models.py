from django.db import models

# Create your models here.

import uuid
# If uuid7 is supported in your environment, replace uuid4 with uuid7
def generate_uuid():
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
