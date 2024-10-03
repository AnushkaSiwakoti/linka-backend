from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from .models import BaseUser  

@csrf_exempt
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

@csrf_exempt
@api_view(['POST'])
def verify_Account(request):
    try:
        user = BaseUser.objects.get(username=request.data.get('username'))

        if user.check_password(request.data.get('password')):
            return JsonResponse({'message': 'User verified successfully'}, status=201)
        else:
            return JsonResponse({'error': 'Incorrect password'}, status=400)

    except BaseUser.DoesNotExist:
        return JsonResponse({'error': 'User does not exist'}, status=404)
