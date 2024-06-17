from django.shortcuts import redirect
from django.views import View
from django.conf import settings
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from oidc_provider.models import Client
from oidc_provider.lib.utils.oauth2 import protected_resource_view
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
import requests
import logging
from .utils import create_or_update_user

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


@method_decorator(protected_resource_view(scopes=['openid', 'email', 'profile']), name='dispatch')
class GoogleCallbackView(View):
    @csrf_exempt  # Disable CSRF for this view
    def get(self, request, *args, **kwargs):
        # This method should not be used for token exchange, hence no implementation required here for token exchange.
        return JsonResponse({'error': 'Method Not Allowed'}, status=405)

    @csrf_exempt  # Disable CSRF for this view
    def post(self, request, *args, **kwargs):
        code = request.POST.get('code')
        state = request.POST.get('state', settings.LOGIN_REDIRECT_URL)
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
        token_response = requests.post(settings.OIDC_TOKEN_ENDPOINT, data=token_data)
        token_response_data = token_response.json()
        logger.info(f"Token response: {token_response_data}")

        if 'error' in token_response_data:
            logger.error(f"Token endpoint error: {token_response_data['error']}")
            return JsonResponse({'error': token_response_data['error']}, status=400)

        # Retrieve user info using access token
        user_info_response = requests.get(
            settings.OIDC_USERINFO_ENDPOINT,
            headers={'Authorization': f"Bearer {token_response_data['access_token']}"}
        )
        user_info = user_info_response.json()
        logger.info(f"User info: {user_info}")

        # Create or update the user in your database
        user = create_or_update_user(user_info)
        logger.info(f"User created/updated: {user}")

        # Redirect to the frontend with the user info or session token
        return redirect(state)
@api_view(['POST'])
def test_auth(request):
    # Print the request body
    logger.info(f"Request Body: {request.data}")

    # Assuming you will process the callbackUrl here and generate an authUrl
    callback_url = request.data.get('callbackUrl')
    
    # Just for demonstration, we'll set a dummy authUrl
    auth_url = "https://accounts.google.com/o/oauth2/auth"

    return Response({"authUrl": auth_url})

