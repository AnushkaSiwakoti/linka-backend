# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# from rest_framework.decorators import api_view
# from .models import BaseUser  

# @csrf_exempt
# @api_view(['POST'])
# def create_Account(request):
#     try:
#         user = BaseUser.objects.create_user(
#             email=request.data.get('email'),
#             username=request.data.get('username'),
#             password=request.data.get('password')
#         )
#         return JsonResponse({'message': 'Account created successfully!'}, status=201)
#     except ValueError as e:
#         return JsonResponse({'error': str(e)}, status=400)

# @csrf_exempt
# @api_view(['POST'])
# def verify_Account(request):
#     try:
#         user = BaseUser.objects.get(username=request.data.get('username'))

#         if user.check_password(request.data.get('password')):
#             return JsonResponse({'message': 'User verified successfully'}, status=201)
#         else:
#             return JsonResponse({'error': 'Incorrect password'}, status=400)

#     except BaseUser.DoesNotExist:
#         return JsonResponse({'error': 'User does not exist'}, status=404)



# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# from rest_framework.decorators import api_view
# from django.contrib.auth import login, authenticate
# from .models import BaseUser


# @api_view(['POST'])
# def create_Account(request):
#     try:
#         user = BaseUser.objects.create_user(
#             email=request.data.get('email'),
#             username=request.data.get('username'),
#             password=request.data.get('password')
#         )
#         return JsonResponse({'message': 'Account created successfully!'}, status=201)
#     except ValueError as e:
#         return JsonResponse({'error': str(e)}, status=400)


# @api_view(['POST'])
# def verify_Account(request):
#     try:
#         username = request.data.get('username')
#         password = request.data.get('password')
        
#         # Use authenticate() to verify the user's credentials
#         user = authenticate(request, username=username, password=password)
        
#         if user is not None:
#             # Log the user in to create an authenticated session
#             login(request, user)
            
#             # Get the session ID and include it in the response
#             session_id = request.session.session_key
#             return JsonResponse({
#                 'message': 'User verified and logged in successfully',
#                 'session_id': session_id
#             }, status=201)
#         else:
#             return JsonResponse({'error': 'Invalid credentials'}, status=400)

#     except BaseUser.DoesNotExist:
#         return JsonResponse({'error': 'User does not exist'}, status=404)




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

@csrf_exempt  # Add csrf_exempt only if you are sure you want to disable CSRF for this endpoint
@api_view(['POST'])
def verify_Account(request):
    try:
        username = request.data.get('username')
        password = request.data.get('password')
        
        # Use authenticate() to verify the user's credentials
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Log the user in to create an authenticated session
            login(request, user)

            # Make sure session key is generated
            request.session.save()
            
            # Get the session ID and include it in the response
            session_id = request.session.session_key
            if not session_id:
                return JsonResponse({'error': 'Failed to generate session ID'}, status=500)
            
            return JsonResponse({
                'message': 'User verified and logged in successfully',
                'session_id': session_id
            }, status=201)
        else:
            return JsonResponse({'error': 'Invalid credentials'}, status=400)

    except BaseUser.DoesNotExist:
        return JsonResponse({'error': 'User does not exist'}, status=404)


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