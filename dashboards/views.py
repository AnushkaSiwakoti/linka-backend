# just to recommit
import os
import traceback
from django.core.exceptions import ValidationError
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
def delete_dashboard(request):
    try:
        # Get dashboard_id from request body
        data = json.loads(request.body)
        dashboard_id = data.get('dashboard_id')
        
        if not dashboard_id:
            return JsonResponse({'error': 'dashboard_id is required'}, status=400)
            
        dashboard = Dashboard.objects.get(id=dashboard_id, user=request.user)
        dashboard.delete()
        return JsonResponse({'message': 'Dashboard deleted successfully'})
    except Dashboard.DoesNotExist:
        return JsonResponse({'error': 'Dashboard not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON in request body'}, status=400)
    except Exception as e:
        return JsonResponse({'error': 'An error occurred while deleting the dashboard'}, status=500)

@csrf_exempt
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([IsAuthenticated])
def deploy_dashboard(request):
    try:
        data = json.loads(request.body)
        dashboard_id = data.get('dashboard_id')
        if not dashboard_id:
            return JsonResponse({'error': 'Dashboard ID is required'}, status=400)

        dashboard = Dashboard.objects.get(id=dashboard_id, user=request.user)
        name = dashboard.name
        state = json.loads(dashboard.state)

        def optimize_positions(state):
            positions = state.get('componentPositions', {})
            components = []
            
            # Convert positions to list and add component types
            for comp_id, pos in positions.items():
                is_table = comp_id == 'table'
                components.append({
                    'id': comp_id,
                    'x': pos['x'],
                    'y': pos['y'],
                    'width': pos.get('width', 700),  # Use saved width or default
                    'height': pos.get('height', 800 if is_table else 400),  # Use saved height or default
                    'is_table': is_table
                })
            
            # Sort components by Y position, then X position
            components.sort(key=lambda c: (c['y'], c['x']))
            
            # Group components into rows (components within 50px Y distance)
            rows = []
            current_row = []
            last_y = None
            
            for comp in components:
                if last_y is None or abs(comp['y'] - last_y) <= 50:
                    current_row.append(comp)
                else:
                    if current_row:
                        rows.append(sorted(current_row, key=lambda c: c['x']))
                    current_row = [comp]
                last_y = comp['y']
            
            if current_row:
                rows.append(sorted(current_row, key=lambda c: c['x']))
            
            # Optimize positions while maintaining relative layout
            optimized_positions = {}
            current_y = 20
            
            for row in rows:
                max_height = max(c['height'] for c in row)
                current_x = 20
                
                for comp in row:
                    # Position the component
                    optimized_positions[comp['id']] = {
                        'x': current_x,
                        'y': current_y,
                        'width': comp['width'],
                        'height': comp['height']
                    }
                    
                    # Update x position for next component with gap
                    current_x = current_x + comp['width'] + 20
                
                # Move to next row with gap
                current_y = current_y + max_height + 20
            
            return optimized_positions

        # Apply position optimization
        optimized_positions = optimize_positions(state)
        state['componentPositions'] = optimized_positions

        # Calculate container dimensions
        max_width = max(pos['x'] + pos['width'] for pos in optimized_positions.values()) + 40
        max_height = max(pos['y'] + pos['height'] for pos in optimized_positions.values()) + 40

        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{name}</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}

                body {{
                    background-color: #000;
                    color: #fff;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    min-height: 100vh;
                    line-height: 1.5;
                    overflow-x: hidden;
                }}

                .deploy-container {{
                    min-height: 100vh;
                    padding: 20px;
                    position: relative;
                }}

                .background-image {{
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100vw;
                    height: 100vh;
                    object-fit: cover;
                    opacity: 0.45;
                    filter: brightness(0.9);
                    z-index: -2;
                }}

                .deploy-container::before {{
                    content: '';
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100vw;
                    height: 100vh;
                    background: rgba(0, 0, 0, 0.6);
                    z-index: -1;
                }}

                .components-container {{
                    width: {max_width}px;
                    min-height: {max_height}px;
                    margin: 0 auto;
                    padding: 20px;
                    position: relative;
                }}

                .component-wrapper {{
                    position: absolute;
                    background: rgba(17, 24, 39, 0.95);
                    border-radius: 12px;
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    overflow: hidden;
                }}

                .component-header {{
                    padding: 16px;
                    background: rgba(0, 0, 0, 0.2);
                    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                }}

                .component-header h3 {{
                    margin: 0;
                    font-size: 1rem;
                    font-weight: 500;
                    color: rgba(255, 255, 255, 0.9);
                }}

                .chart-wrapper {{
                    height: calc(100% - 53px);
                    padding: 16px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }}

                .chart-wrapper canvas {{
                    width: 100% !important;
                    height: 100% !important;
                }}

                .table-wrapper {{
                    height: calc(100% - 53px);
                    display: flex;
                    flex-direction: column;
                }}

                .table-content {{
                    flex: 1;
                    overflow: auto;
                    padding: 16px;
                }}

                .data-table {{
                    width: 100%;
                    border-collapse: collapse;
                }}

                .data-table th,
                .data-table td {{
                    padding: 12px;
                    text-align: left;
                    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                }}

                .data-table th {{
                    background: rgba(0, 0, 0, 0.2);
                    position: sticky;
                    top: 0;
                    z-index: 1;
                    font-weight: 500;
                }}

                .pagination {{
                    padding: 16px;
                    display: flex;
                    justify-content: center;
                    gap: 16px;
                    align-items: center;
                    background: rgba(0, 0, 0, 0.2);
                }}

                .pagination button {{
                    padding: 8px 16px;
                    background: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 4px;
                    color: white;
                    cursor: pointer;
                }}

                .pagination button:disabled {{
                    opacity: 0.5;
                    cursor: not-allowed;
                }}

                @media (max-width: {max_width + 40}px) {{
                    .deploy-container {{
                        overflow-x: auto;
                        padding: 20px 0;
                    }}
                    
                    .components-container {{
                        margin: 0 20px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="deploy-container">
                <div id="componentsContainer" class="components-container"></div>
            </div>
            <script>
                const dashboardState = {json.dumps(state)};
                const ROWS_PER_PAGE = 10;

                function createChart(chartData, type) {{
                    const ctx = document.createElement('canvas');
                    ctx.style.maxHeight = '100%';
                    
                    new Chart(ctx, {{
                        type: type,
                        data: chartData.data,
                        options: {{
                            ...chartData.options,
                            maintainAspectRatio: false,
                            responsive: true,
                            plugins: {{
                                legend: {{
                                    position: 'top',
                                    labels: {{ 
                                        color: '#fff',
                                        padding: 20,
                                        font: {{
                                            size: 11
                                        }}
                                    }}
                                }}
                            }},
                            scales: {{
                                x: {{
                                    grid: {{ color: 'rgba(255,255,255,0.1)' }},
                                    ticks: {{ 
                                        color: '#fff',
                                        font: {{ size: 11 }}
                                    }}
                                }},
                                y: {{
                                    grid: {{ color: 'rgba(255,255,255,0.1)' }},
                                    ticks: {{ 
                                        color: '#fff',
                                        font: {{ size: 11 }}
                                    }}
                                }}
                            }}
                        }}
                    }});
                    return ctx;
                }}

                function createTable(data, columns) {{
                    const wrapper = document.createElement('div');
                    wrapper.className = 'table-wrapper';

                    const content = document.createElement('div');
                    content.className = 'table-content';

                    const table = document.createElement('table');
                    table.className = 'data-table';

                    const thead = document.createElement('thead');
                    const headerRow = document.createElement('tr');
                    columns.forEach(column => {{
                        const th = document.createElement('th');
                        th.textContent = column;
                        headerRow.appendChild(th);
                    }});
                    thead.appendChild(headerRow);
                    table.appendChild(thead);

                    const tbody = document.createElement('tbody');
                    data.slice(0, ROWS_PER_PAGE).forEach(row => {{
                        const tr = document.createElement('tr');
                        columns.forEach(column => {{
                            const td = document.createElement('td');
                            td.textContent = row[column];
                            tr.appendChild(td);
                        }});
                        tbody.appendChild(tr);
                    }});
                    table.appendChild(tbody);

                    content.appendChild(table);
                    wrapper.appendChild(content);

                    const pagination = document.createElement('div');
                    pagination.className = 'pagination';
                    pagination.innerHTML = `
                        <button disabled>Previous</button>
                        <span>Page 1 of ${{Math.ceil(data.length / ROWS_PER_PAGE)}}</span>
                        <button>Next</button>
                    `;
                    wrapper.appendChild(pagination);

                    return wrapper;
                }}

                function renderComponent(componentId) {{
                    const chart = dashboardState.charts?.find(c => c.id === componentId);
                    const isTable = componentId === 'table';
                    const position = dashboardState.componentPositions[componentId];

                    if (!position) return null;

                    const wrapper = document.createElement('div');
                    wrapper.className = 'component-wrapper';
                    
                    // Apply exact position and size
                    wrapper.style.width = `${{position.width}}px`;
                    wrapper.style.height = `${{position.height}}px`;
                    wrapper.style.transform = `translate(${{position.x}}px, ${{position.y}}px)`;

                    const header = document.createElement('div');
                    header.className = 'component-header';
                    header.innerHTML = `<h3>${{isTable ? 'Data Table' : `${{chart?.type === 'pie' ? 'Category' : chart?.chartType}} Distribution`}}</h3>`;
                    wrapper.appendChild(header);

                    if (isTable) {{
                        wrapper.appendChild(createTable(dashboardState.data, dashboardState.columns));
                    }} else if (chart) {{
                        const chartWrapper = document.createElement('div');
                        chartWrapper.className = 'chart-wrapper';
                        chartWrapper.appendChild(createChart(chart, chart.type));
                        wrapper.appendChild(chartWrapper);
                    }}

                    return wrapper;
                }}

                document.addEventListener('DOMContentLoaded', () => {{
                    const container = document.getElementById('componentsContainer');
                    
                    // Render components in saved order
                    dashboardState.componentOrder.forEach(componentId => {{
                        const component = renderComponent(componentId);
                        if (component) {{
                            container.appendChild(component);
                        }}
                    }});
                }});
            </script>
        </body>
        </html>
        """

        # local: deployment_directory = os.path.join(os.getcwd(), 'deployments')
        
        # if not os.path.exists(deployment_directory):
        #     os.makedirs(deployment_directory)
        #     print(f"Deployment directory: {deployment_directory}")  # Debug statement

        
        deployment_directory = '/app/deployments'

        file_name = f"dashboard_{request.user.id}_{dashboard_id}.html"
        file_path = os.path.join(deployment_directory, file_name)
        print(f"File path for deployment: {file_path}")  # Debug statement

        try:
            with open(file_path, 'w') as file:
                file.write(html_content)
            print(f"[DEBUG] Successfully created HTML file at: {file_path}")
        except Exception as file_creation_error:
            print(f"[ERROR] Failed to create HTML file at {file_path}: {file_creation_error}")
            traceback.print_exc()
            
        deployed_url = f"{request.build_absolute_uri('/')[:-1]}/deployments/{file_name}"
        
        dashboard.deployed_url = deployed_url
        dashboard.save()

        return JsonResponse({
            'message': 'Dashboard deployed successfully',
            'deployed_url': deployed_url
        })

    except Exception as e:
        print(f"Error deploying dashboard: {str(e)}")
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)
