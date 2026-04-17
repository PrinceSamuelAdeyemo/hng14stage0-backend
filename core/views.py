
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


# Simple health check endpoint
@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
	"""Health check endpoint - no database required"""
	try:
		from django.db import connection
		with connection.cursor() as cursor:
			cursor.execute("SELECT 1")
		db_status = "OK"
	except Exception as e:
		db_status = str(e)
	
	resp = Response({
		"status": "success",
		"message": "API is running",
		"database": db_status
	}, status=200)
	return add_cors_header(resp)


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
		
		# Validate name - check if it's an integer or float first (numeric type)
		if isinstance(name, (int, float)):
			resp = Response({"status": "error", "message": "Invalid data type"}, status=422)
			return add_cors_header(resp)
		
		# Validate name - missing or empty or not a string
		if not name or not isinstance(name, str) or not name.strip():
			resp = Response({"status": "error", "message": "Missing or empty name"}, status=400)
			return add_cors_header(resp)
		
		# Try to convert to see if it's a pure number string
		try:
			_ = int(name.strip())
			resp = Response({"status": "error", "message": "Invalid data type"}, status=422)
			return add_cors_header(resp)
		except (ValueError, AttributeError):
			pass  # Not a number, continue
		
		name = name.strip().lower()
		
		# Check for existing profile
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
		except Exception as e:
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
		except Exception as e:
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
		except Exception as e:
			resp = Response({"status": "error", "message": "Nationalize returned an invalid response"}, status=502)
			return add_cors_header(resp)
		
		countries = n_data.get("country", [])
		if not countries or len(countries) == 0:
			resp = Response({"status": "error", "message": "Nationalize returned an invalid response"}, status=502)
			return add_cors_header(resp)
		
		# Safely get top country
		try:
			top_country = max(countries, key=lambda c: float(c.get("probability", 0)))
		except (ValueError, TypeError, KeyError):
			resp = Response({"status": "error", "message": "Nationalize returned an invalid response"}, status=502)
			return add_cors_header(resp)
		
		# Extract and validate all data
		age = a_data.get("age")
		if age is None:
			resp = Response({"status": "error", "message": "Agify returned an invalid response"}, status=502)
			return add_cors_header(resp)
		
		age_group = classify_age_group(age)
		gender = g_data.get("gender", "")
		gender_probability = float(g_data.get("probability", 0))
		sample_size = int(g_data.get("count", 0))
		country_id = top_country.get("country_id", "")
		country_probability = float(top_country.get("probability", 0))
		
		try:
			# Use get_or_create for atomic operation (handles race conditions)
			profile, created = Profile.objects.get_or_create(
				name=name,
				defaults={
					'gender': gender,
					'gender_probability': gender_probability,
					'sample_size': sample_size,
					'age': age,
					'age_group': age_group,
					'country_id': country_id,
					'country_probability': country_probability,
				}
			)
			data = ProfileSerializer(profile).data
			if created:
				resp = Response({"status": "success", "data": data}, status=201)
			else:
				resp = Response({"status": "success", "message": "Profile already exists", "data": data}, status=200)
			return add_cors_header(resp)
		except Exception as e:
			import sys
			import traceback
			exc_type, exc_value, exc_traceback = sys.exc_info()
			error_msg = str(e)
			print(f"ERROR: {error_msg}", file=sys.stderr)
			traceback.print_exc(file=sys.stderr)
			resp = Response({"status": "error", "message": f"Failed to save profile: {error_msg[:100]}"}, status=500)
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
