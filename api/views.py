from django.shortcuts import redirect
from django.views import View
from django.conf import settings
from django.http import JsonResponse, HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from oidc_provider.models import Client
from oidc_provider.lib.utils.oauth2 import protected_resource_view
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
import requests
import json
import logging
import urllib.parse
from .utils import create_or_update_user
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User 

logger = logging.getLogger(__name__)


class InitiateGoogleLoginView(APIView):
    @csrf_exempt  # Disable CSRF for this view
    def post(self, request):
        callback_url = request.data.get('callbackUrl', settings.LOGIN_REDIRECT_URL)
        frontend_redirect_url = settings.LOGIN_REDIRECT_URL + '/settings'
        try:
            client = Client.objects.get(client_id=settings.OIDC_CLIENT_ID)
            logger.info(f"Client found: {client}")

            auth_url = (
                f"{settings.OIDC_AUTHORIZATION_ENDPOINT}?response_type=code"
                f"&client_id={client.client_id}"
                f"&redirect_uri={client.redirect_uris[0]}"
                f"&scope=openid email profile"
                f"&state={frontend_redirect_url}"
            )
            logger.info(f"Generated auth URL: {auth_url}")

            return Response({'authUrl': auth_url})
        except Client.DoesNotExist:
            logger.error("OIDC Client not found.")
            return JsonResponse({'error': 'OIDC Client not found'}, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class GoogleCallbackView(View):
    def get(self, request, *args, **kwargs):
        code = request.GET.get('code')
        state = request.GET.get('state', settings.LOGIN_REDIRECT_URL)
        logger.info(f"Received code: {code} and state: {state}")

        if not code:
            return JsonResponse({'error': 'No code provided'}, status=400)

        token_data = {
            'code': code,
            'client_id': settings.OIDC_CLIENT_ID,
            'client_secret': settings.OIDC_CLIENT_SECRET,
            'redirect_uri': settings.OIDC_PROVIDERS['google']['redirect_uris'][0],
            'grant_type': 'authorization_code',
        }
        logger.info(f"Token data: {token_data}")

        # Exchange authorization code for access token
        try:
            token_response = requests.post(settings.OIDC_TOKEN_ENDPOINT, data=token_data)
            token_response.raise_for_status()
            token_response_data = token_response.json()
            logger.info(f"Token response: {token_response_data}")
        except requests.RequestException as e:
            logger.error(f"Token request failed: {e}")
            return JsonResponse({'error': 'Token request failed'}, status=400)

        if 'error' in token_response_data:
            logger.error(f"Token endpoint error: {token_response_data['error']}")
            return JsonResponse({'error': token_response_data['error']}, status=400)

        access_token = token_response_data.get('access_token')
        if not access_token:
            logger.error("No access token found in the response")
            return JsonResponse({'error': 'No access token found'}, status=400)

        # Retrieve user info using access token
        try:
            user_info_response = requests.get(
                settings.OIDC_USERINFO_ENDPOINT,
                headers={'Authorization': f"Bearer {access_token}"}
            )
            user_info_response.raise_for_status()
            user_info = user_info_response.json()
            logger.info(f"User info: {user_info}")
        except requests.RequestException as e:
            logger.error(f"User info request failed: {e}")
            return JsonResponse({'error': 'User info request failed'}, status=400)

        # Create or update the user in your database
        try:
            user = create_or_update_user(user_info)
            logger.info(f"User created/updated: {user}")
        except Exception as e:
            logger.error(f"Error creating/updating user: {e}")
            return JsonResponse({'error': 'Error creating/updating user'}, status=500)

        # Manage session here
        request.session['user'] = user_info

        # Redirect to the frontend with the user info or session token
        frontend_redirect_url = f"{settings.LOGIN_REDIRECT_URL}/api/loguser"
        redirect_url_with_params = f"{frontend_redirect_url}?session_token={access_token}&user_info={urllib.parse.quote_plus(json.dumps(user_info))}"
        return HttpResponseRedirect(redirect_url_with_params)

    
def logout_view(request):
    id_token_hint = request.session.get('id_token')
    post_logout_redirect_uri = settings.LOGIN_REDIRECT_URL + '/logged-out/'

    logout_url = (
        f"{settings.OIDC_LOGOUT_ENDPOINT}?"
        f"id_token_hint={id_token_hint}&"
        f"post_logout_redirect_uri={post_logout_redirect_uri}"
    )
    return redirect(logout_url)    


@csrf_exempt
@require_http_methods(["GET"])
def get_user_by_email(request):
    if request.method == "GET":
        email = request.GET.get("email", "")
        if not email:
            return JsonResponse({"error": "Email parameter is required"}, status=400)
       

        email = urllib.parse.unquote(email) 
        
 
        try:
            user = User.objects.get(email=email)
            user_data = {
                "id": str(user.id),
                "name": user.first_name,
                "email": user.email,
            }
            return JsonResponse(user_data)
        except User.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Method not allowed"}, status=405)

@csrf_exempt
@require_http_methods(["GET"])
def get_user_by_id(request):
    if request.method == "GET":
        user_id = request.GET.get("id", "")
        if not user_id:
            return JsonResponse({"error": "User ID parameter is required"}, status=400)

        try:
            user = User.objects.get(username=user_id)
            user_data = {
                "id": str(user.id),
                "name": user.first_name,
                "email": user.email,
            }
            return JsonResponse(user_data)
        except User.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Method not allowed"}, status=405)


