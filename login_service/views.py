from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from django.contrib.auth import logout
from django.contrib.auth import login, authenticate
from .models import BaseUser

@csrf_exempt  # Add csrf_exempt only if you are sure you want to disable CSRF for this endpoint
@api_view(['POST'])
def create_Account(request):
    try:
        user = BaseUser.objects.create_user(
            email=request.data.get('email'),
            username=request.data.get('username'),
            password=request.data.get('password')
        )
        return JsonResponse({'message': 'Account created successfully!'}, status=201)
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)

@api_view(['POST'])
def verify_Account(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(request, username=username, password=password)
    
    if user:
        login(request, user)
        return JsonResponse({
            'username': user.username,
            'sessionid': request.session.session_key
        }, status=200)
    return JsonResponse({'error': 'Invalid credentials'}, status=401)

@csrf_exempt  # Only use if you are sure about bypassing CSRF protection for this view
def logout_view(request):
    # Log out the user and invalidate the session
    logout(request)

    # Create a response to remove cookies
    response = JsonResponse({'message': 'Logged out successfully'})

    # Delete sessionid and csrftoken cookies
    response.delete_cookie('sessionid', path='/', domain=None)
    response.delete_cookie('csrftoken', path='/', domain=None)

    return response