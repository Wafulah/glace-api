# utils.py

from django.contrib.auth.models import User

def create_or_update_user(user_info):
    """
    Create or update a user based on the information obtained from Google.
    """
    email = user_info.get('email')
    first_name = user_info.get('given_name')
    last_name = user_info.get('family_name')
    sub=user_info.get('sub')

    user, created = User.objects.update_or_create(
        email=email,
        
        defaults={
            'first_name': first_name,
            'last_name': last_name,
            'username': sub,
        }
    )
    return user
