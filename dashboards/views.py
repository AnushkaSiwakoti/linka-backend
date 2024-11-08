
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from .models import Dashboard
import json
from django.core.exceptions import ValidationError

class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        # Disable CSRF token checking
        return

# Custom user authentication function
def verify_user(request):
    if request.user.is_authenticated:
        return True, request.user
    else:
        return False, JsonResponse({
            'error': 'Authentication required',
            'redirect_url': '/verify-account/'
        }, status=401)

# @csrf_exempt
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([IsAuthenticated])
def save_dashboard(request):
    print("Request Method:", request.method)
    print("Request URL:", request.build_absolute_uri())
    print("Request Headers:", request.headers)
    print("Request Body:", request.body.decode('utf-8'))

    try:
        data = json.loads(request.body)
        name = data.get('name')
        if not name:
            return JsonResponse({'error': 'Dashboard name is required'}, status=400)

        state = data.get('state')
        if not state:
            return JsonResponse({'error': 'Dashboard state is required'}, status=400)

        dashboard, created = Dashboard.objects.update_or_create(
            user=request.user,
            name=name,
            defaults={'state': json.dumps(state)}
        )

        return JsonResponse({
            'message': 'Dashboard saved successfully',
            'dashboard_id': dashboard.id,
            'created': created
        })
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except ValidationError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([IsAuthenticated])
def list_dashboards(request):
    try:
        dashboards = Dashboard.objects.filter(user=request.user).values(
            'id', 
            'name', 
            'created_at', 
            'updated_at'
        ).order_by('-updated_at')

        return JsonResponse({
            'dashboards': list(dashboards),
            'count': len(dashboards)
        }, safe=False)
    except Exception as e:
        return JsonResponse({'error': 'An error occurred while fetching dashboards'}, status=500)

@csrf_exempt
@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([IsAuthenticated])
def get_dashboard(request, dashboard_id):
    try:
        dashboard = Dashboard.objects.get(id=dashboard_id, user=request.user)
        return JsonResponse({
            'id': dashboard.id,
            'name': dashboard.name,
            'state': json.loads(dashboard.state),
            'created_at': dashboard.created_at,
            'updated_at': dashboard.updated_at
        })
    except Dashboard.DoesNotExist:
        return JsonResponse({'error': 'Dashboard not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid dashboard state'}, status=500)
    except Exception as e:
        return JsonResponse({'error': 'An error occurred while fetching the dashboard'}, status=500)

@csrf_exempt
@api_view(['DELETE'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([IsAuthenticated])
def delete_dashboard(request, dashboard_id):
    try:
        dashboard = Dashboard.objects.get(id=dashboard_id, user=request.user)
        dashboard.delete()
        return JsonResponse({'message': 'Dashboard deleted successfully'})
    except Dashboard.DoesNotExist:
        return JsonResponse({'error': 'Dashboard not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': 'An error occurred while deleting the dashboard'}, status=500)