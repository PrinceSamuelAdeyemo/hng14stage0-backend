
import requests
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import datetime

@csrf_exempt
@require_GET
def classify_name(request):
	# CORS header
	cors_headers = {'Access-Control-Allow-Origin': '*'}
	name = request.GET.get('name', None)
	if name is None or (isinstance(name, str) and name.strip() == ''):
		return JsonResponse({"status": "error", "message": "Missing or empty name parameter"}, status=400, headers=cors_headers)
	if not isinstance(name, str):
		return JsonResponse({"status": "error", "message": "name is not a string"}, status=422, headers=cors_headers)
	try:
		resp = requests.get('https://api.genderize.io', params={'name': name}, timeout=3)
		if resp.status_code != 200:
			return JsonResponse({"status": "error", "message": "Upstream API error"}, status=502, headers=cors_headers)
		data = resp.json()
		gender = data.get('gender')
		probability = data.get('probability')
		count = data.get('count')
		# Edge case: no prediction
		if gender is None or count == 0:
			return JsonResponse({"status": "error", "message": "No prediction available for the provided name"}, status=200, headers=cors_headers)
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
		return JsonResponse({
			"status": "success",
			"data": {
				"name": name,
				"gender": gender,
				"probability": probability_val,
				"sample_size": sample_size,
				"is_confident": is_confident,
				"processed_at": processed_at
			}
		}, status=200, headers=cors_headers)
	except requests.exceptions.RequestException:
		return JsonResponse({"status": "error", "message": "Upstream or server failure"}, status=500, headers=cors_headers)
