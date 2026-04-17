
import requests
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from django.db.models import Q
from .models import Profile
from .serializers import ProfileSerializer
from rest_framework.permissions import AllowAny
import json


# DRF-based classify_name endpoint (if still needed)
@api_view(["GET"])
@permission_classes([AllowAny])
def classify_name(request):
	name = request.GET.get('name', None)
	response = Response()
	response['Access-Control-Allow-Origin'] = '*'
	if name is None or (isinstance(name, str) and name.strip() == ''):
		response.data = {"status": "error", "message": "Missing or empty name parameter"}
		response.status_code = 400
		return response
	if not isinstance(name, str):
		response.data = {"status": "error", "message": "name is not a string"}
		response.status_code = 422
		return response
	try:
		resp = requests.get('https://api.genderize.io', params={'name': name}, timeout=3)
		if resp.status_code != 200:
			response.data = {"status": "error", "message": "Upstream API error"}
			response.status_code = 502
			return response
		data = resp.json()
		gender = data.get('gender')
		probability = data.get('probability')
		count = data.get('count')
		# Edge case: no prediction
		if gender is None or count == 0:
			response.data = {"status": "error", "message": "No prediction available for the provided name"}
			response.status_code = 200
			return response
		# Compute is_confident
		try:
			probability_val = float(probability)
		except (TypeError, ValueError):
			probability_val = 0.0
		try:
			sample_size = int(count)
		except (TypeError, ValueError):
			sample_size = 0
		is_confident = probability_val >= 0.7 and sample_size >= 100
		processed_at = datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'
		response.data = {
			"status": "success",
			"data": {
				"name": name,
				"gender": gender,
				"probability": probability_val,
				"sample_size": sample_size,
				"is_confident": is_confident,
				"processed_at": processed_at
			}
		}
		response.status_code = 200
		return response
	except requests.exceptions.RequestException:
		response.data = {"status": "error", "message": "Upstream or server failure"}
		response.status_code = 500
		return response

def add_cors_header(response):
	response["Access-Control-Allow-Origin"] = "*"
	response["Access-Control-Allow-Methods"] = "GET, POST, DELETE, OPTIONS"
	response["Access-Control-Allow-Headers"] = "Content-Type"
	return response

def get_request_data(request):
	"""
	Safely extract JSON data from request, handling Vercel serverless environment.
	Tries multiple methods to ensure data is properly parsed.
	"""
	# Try DRF's request.data first (normal case)
	if request.data:
		return request.data
	
	# Try parsing request.body directly (for serverless environments)
	try:
		if request.body:
			return json.loads(request.body)
	except (json.JSONDecodeError, AttributeError):
		pass
	
	# Try POST data
	if request.POST:
		return request.POST
	
	# Return empty dict if nothing found
	return {}

def classify_age_group(age):
	if age is None:
		return None
	if 0 <= age <= 12:
		return "child"
	elif 13 <= age <= 19:
		return "teenager"
	elif 20 <= age <= 59:
		return "adult"
	elif age >= 60:
		return "senior"
	return None

from rest_framework.permissions import AllowAny

class ProfileListCreateView(APIView):
	permission_classes = [AllowAny]
	def get(self, request):
		gender = request.GET.get('gender')
		country_id = request.GET.get('country_id')
		age_group = request.GET.get('age_group')
		filters = Q()
		if gender:
			filters &= Q(gender__iexact=gender)
		if country_id:
			filters &= Q(country_id__iexact=country_id)
		if age_group:
			filters &= Q(age_group__iexact=age_group)
		profiles = Profile.objects.filter(filters)
		data = [
			{
				"id": str(p.id),
				"name": p.name,
				"gender": p.gender,
				"age": p.age,
				"age_group": p.age_group,
				"country_id": p.country_id,
			}
			for p in profiles
		]
		resp = Response({"status": "success", "count": len(data), "data": data}, status=200)
		return add_cors_header(resp)

	def post(self, request):
		# Get request data with fallback for serverless environments
		data = get_request_data(request)
		name = data.get("name") if isinstance(data, dict) else None
		
		if not name or not isinstance(name, str) or not name.strip():
			resp = Response({"status": "error", "message": "Missing or empty name"}, status=400)
			return add_cors_header(resp)
		name = name.strip().lower()
		
		# Use get_or_create (atomic) to avoid race conditions on concurrent requests
		existing = Profile.objects.filter(name=name).first()
		if existing:
			data = ProfileSerializer(existing).data
			resp = Response({"status": "success", "message": "Profile already exists", "data": data}, status=200)
			return add_cors_header(resp)
		
		# Call Genderize
		g_url = f"https://api.genderize.io?name={name}"
		try:
			g_res = requests.get(g_url, timeout=5)
			g_data = g_res.json()
		except Exception:
			resp = Response({"status": "error", "message": "Genderize returned an invalid response"}, status=502)
			return add_cors_header(resp)
		if not g_data.get("gender") or g_data.get("count", 0) == 0:
			resp = Response({"status": "error", "message": "Genderize returned an invalid response"}, status=502)
			return add_cors_header(resp)
		# Call Agify
		a_url = f"https://api.agify.io?name={name}"
		try:
			a_res = requests.get(a_url, timeout=5)
			a_data = a_res.json()
		except Exception:
			resp = Response({"status": "error", "message": "Agify returned an invalid response"}, status=502)
			return add_cors_header(resp)
		if a_data.get("age") is None:
			resp = Response({"status": "error", "message": "Agify returned an invalid response"}, status=502)
			return add_cors_header(resp)
		# Call Nationalize
		n_url = f"https://api.nationalize.io?name={name}"
		try:
			n_res = requests.get(n_url, timeout=5)
			n_data = n_res.json()
		except Exception:
			resp = Response({"status": "error", "message": "Nationalize returned an invalid response"}, status=502)
			return add_cors_header(resp)
		countries = n_data.get("country", [])
		if not countries:
			resp = Response({"status": "error", "message": "Nationalize returned an invalid response"}, status=502)
			return add_cors_header(resp)
		top_country = max(countries, key=lambda c: c.get("probability", 0))
		# Classification
		age = a_data["age"]
		age_group = classify_age_group(age)
		
		try:
			# Use get_or_create for atomic operation (handles race conditions)
			profile, created = Profile.objects.get_or_create(
				name=name,
				defaults={
					'gender': g_data["gender"],
					'gender_probability': g_data["probability"],
					'sample_size': g_data["count"],
					'age': age,
					'age_group': age_group,
					'country_id': top_country["country_id"],
					'country_probability': top_country["probability"],
				}
			)
			data = ProfileSerializer(profile).data
			if created:
				resp = Response({"status": "success", "data": data}, status=201)
			else:
				resp = Response({"status": "success", "message": "Profile already exists", "data": data}, status=200)
			return add_cors_header(resp)
		except Exception as e:
			resp = Response({"status": "error", "message": "Failed to save profile"}, status=500)
			return add_cors_header(resp)

class ProfileDetailView(APIView):
	permission_classes = [AllowAny]
	def get(self, request, pk):
		profile = get_object_or_404(Profile, pk=pk)
		data = ProfileSerializer(profile).data
		resp = Response({"status": "success", "data": data}, status=200)
		return add_cors_header(resp)

	def delete(self, request, pk):
		profile = get_object_or_404(Profile, pk=pk)
		profile.delete()
		resp = Response(status=204)
		return add_cors_header(resp)
