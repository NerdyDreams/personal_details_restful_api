from django.shortcuts import render

# Create your views here.

import re
import logging
from django.core.cache import cache
from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view
from uuid import uuid4

# In-memory data store
registrations = {}

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate limit configurations
RATE_LIMIT = 5  # requests per minute per IP
RATE_LIMIT_KEY = "rate_limit_{}"

# Helper function for rate limiting
def rate_limit(request):
    ip = request.META.get('REMOTE_ADDR')
    key = RATE_LIMIT_KEY.format(ip)
    requests = cache.get(key, 0)
    if requests >= RATE_LIMIT:
        return True
    cache.set(key, requests + 1, timeout=60)  # Rate limit window is 60 seconds
    return False

# POST /register endpoint
@api_view(['POST'])
def register(request):
    if rate_limit(request):
        return JsonResponse({"error": "Rate limit exceeded"}, status=status.HTTP_429_TOO_MANY_REQUESTS)

    phone_number = request.data.get("phone_number")
    mobile_network = request.data.get("mobile_network")
    message = request.data.get("message")
    ref_code = request.data.get("ref_code")

    # Validations
    if not re.match(r'^\d{11}$', phone_number):
        return JsonResponse({"error": "Phone number must be 11 digits"}, status=status.HTTP_400_BAD_REQUEST)
    if mobile_network not in ["mtn", "airtel", "9mobile", "glo"]:
        return JsonResponse({"error": "Invalid mobile network"}, status=status.HTTP_400_BAD_REQUEST)
    if not re.match(r'^[a-zA-Z0-9]{16,}$', ref_code) or ref_code in registrations:
        return JsonResponse({"error": "Invalid or duplicate ref_code"}, status=status.HTTP_400_BAD_REQUEST)
    
    # Register new entry
    registrations[ref_code] = {
        "phone_number": phone_number,
        "mobile_network": mobile_network,
        "message": message,
        "status": "successful"
    }

    # Logging
    logger.info(f"Registered user with ref_code {ref_code}")
    return JsonResponse({"ref_code": ref_code, "status": "successful"}, status=status.HTTP_201_CREATED)

# GET /status/<ref_code> endpoint
@api_view(['GET'])
def check_status(request, ref_code):
    if rate_limit(request):
        return JsonResponse({"error": "Rate limit exceeded"}, status=status.HTTP_429_TOO_MANY_REQUESTS)

    registration = registrations.get(ref_code)
    if not registration:
        return JsonResponse({"error": "Registration not found"}, status=status.HTTP_404_NOT_FOUND)
    
    # Logging
    logger.info(f"Checked status for ref_code {ref_code}")
    return JsonResponse({"ref_code": ref_code, "status": registration["status"]}, status=status.HTTP_200_OK)

# PUT /update/<ref_code> endpoint
@api_view(['PUT'])
def update_message(request, ref_code):
    if rate_limit(request):
        return JsonResponse({"error": "Rate limit exceeded"}, status=status.HTTP_429_TOO_MANY_REQUESTS)

    registration = registrations.get(ref_code)
    if not registration:
        return JsonResponse({"error": "Registration not found"}, status=status.HTTP_404_NOT_FOUND)
    
    message = request.data.get("message")
    if not message:
        return JsonResponse({"error": "Message is required"}, status=status.HTTP_400_BAD_REQUEST)

    # Update message
    registration["message"] = message

    # Logging
    logger.info(f"Updated message for ref_code {ref_code}")
    return JsonResponse({"ref_code": ref_code, "status": "updated"}, status=status.HTTP_200_OK)
