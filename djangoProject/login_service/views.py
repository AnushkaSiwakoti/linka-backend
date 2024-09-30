from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from login_service.models import CustomUserManager

@csrf_exempt
@api_view(['POST'])
def create_Account(request):
    user_manager = CustomUserManager()

    try:
        user = user_manager.create_user(
            email=request.data.get('email'),
            username=request.data.get('username'),
            password=request.data.get('password')
        )
        return JsonResponse({'message': 'Account created successfully!'}, status=201)
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@api_view(['POST'])
def verify_Account(request):
    user_manager = CustomUserManager()
    
    try:
        user = user_manager.verify_user(
            username=request.data.get('username'),
            password=request.data.get('password')
        )
        return JsonResponse({'message': 'User verified successfully'}, status=200)
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@api_view(['GET'])
def get_routes(request):
    routes = [
        '/create-account/',
        '/verify-account/'
    ]
    return JsonResponse(routes, safe=False)
