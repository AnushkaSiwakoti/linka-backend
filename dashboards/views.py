# just to recommit
import os
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

        # Generate the HTML content for the dashboard
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{name} - Dashboard</title>
            <link rel="stylesheet" href="/deployments/deploy.css">
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

        </head>
        <body>
            <div class="container mt-4">
                <h1>{name}</h1>
                <div id="chartsContainer" style="position: relative;"></div>
                <div id="tableContainer"></div>
            </div>
            
            <script>
                const dashboardState = {json.dumps(state)};
                
                // Render the charts
                function renderCharts() {{
                    const container = document.getElementById('chartsContainer');
                    container.innerHTML = ''; // Clear existing charts

                    dashboardState.charts.forEach((chart) => {{
                        const chartDiv = document.createElement('div');
                        chartDiv.classList.add('chart-item');
                        chartDiv.style.left = `${{dashboardState.componentPositions[chart.id].x || 20}}px`;
                        chartDiv.style.top = `${{dashboardState.componentPositions[chart.id].y || 20}}px`;
                        chartDiv.style.width = `${{dashboardState.componentPositions[chart.id].width || 700}}px`;
                        chartDiv.style.height = `${{dashboardState.componentPositions[chart.id].height || 400}}px`;
                        
                        const canvas = document.createElement('canvas');
                        chartDiv.appendChild(canvas);
                        container.appendChild(chartDiv);

                        const chartConfig = {{
                            type: chart.type,
                            data: chart.data,
                            options: Object.assign({{}}, chart.options, {{
                                responsive: true,
                                maintainAspectRatio: false
                            }})
                        }};

                        new Chart(canvas, chartConfig);
                    }});
                }}
                
                // Render the table with pagination, sorting, and filters
                function renderTable() {{
                    if (!dashboardState.showTable) return;

                    const container = document.getElementById('tableContainer');
                    container.innerHTML = ''; // Clear existing table
                    const tableWrapper = document.createElement('div');
                    tableWrapper.className = 'table-section';

                    const table = document.createElement('table');
                    table.className = 'table table-striped data-table';

                    // Create table header
                    const thead = document.createElement('thead');
                    const headerRow = document.createElement('tr');
                    dashboardState.columns.forEach(column => {{
                        const th = document.createElement('th');
                        th.textContent = column;
                        th.style.cursor = 'pointer';

                        // Add sorting functionality
                        th.addEventListener('click', () => {{
                            // Sort table based on column clicked
                            if (dashboardState.tableFilters.sortColumn === column) {{
                                dashboardState.tableFilters.sortDirection = dashboardState.tableFilters.sortDirection === 'asc' ? 'desc' : 'asc';
                            }} else {{
                                dashboardState.tableFilters.sortColumn = column;
                                dashboardState.tableFilters.sortDirection = 'asc';
                            }}
                            renderTable(); // Re-render table after sorting
                        }});

                        // Add sort direction indicator
                        if (dashboardState.tableFilters.sortColumn === column) {{
                            const sortIndicator = document.createElement('span');
                            sortIndicator.textContent = dashboardState.tableFilters.sortDirection === 'asc' ? ' ↑' : ' ↓';
                            th.appendChild(sortIndicator);
                        }}
                        
                        headerRow.appendChild(th);
                    }});
                    thead.appendChild(headerRow);
                    table.appendChild(thead);

                    // Apply filters and sort table data
                    const filteredData = applyTableFilters(dashboardState.data);

                    // Create table body with pagination
                    const startIndex = dashboardState.tableFilters.pageIndex * dashboardState.tableFilters.rowsPerPage;
                    const endIndex = startIndex + dashboardState.tableFilters.rowsPerPage;
                    const pageData = filteredData.slice(startIndex, endIndex);

                    const tbody = document.createElement('tbody');
                    pageData.forEach(row => {{
                        const tr = document.createElement('tr');
                        dashboardState.columns.forEach(column => {{
                            const td = document.createElement('td');
                            td.textContent = row[column];
                            tr.appendChild(td);
                        }});
                        tbody.appendChild(tr);
                    }});
                    table.appendChild(tbody);

                    tableWrapper.appendChild(table);

                    // Pagination controls
                    const paginationControls = document.createElement('div');
                    paginationControls.className = 'pagination';

                    const prevButton = document.createElement('button');
                    prevButton.textContent = 'Previous';
                    prevButton.disabled = dashboardState.tableFilters.pageIndex === 0;
                    prevButton.onclick = () => {{
                        dashboardState.tableFilters.pageIndex = Math.max(0, dashboardState.tableFilters.pageIndex - 1);
                        renderTable();
                    }};
                    paginationControls.appendChild(prevButton);

                    const pageInfo = document.createElement('span');
                    pageInfo.textContent = `Page ${{dashboardState.tableFilters.pageIndex + 1}} of ${{Math.ceil(filteredData.length / dashboardState.tableFilters.rowsPerPage)}}`;
                    paginationControls.appendChild(pageInfo);

                    const nextButton = document.createElement('button');
                    nextButton.textContent = 'Next';
                    nextButton.disabled = endIndex >= filteredData.length;
                    nextButton.onclick = () => {{
                        if (dashboardState.tableFilters.pageIndex + 1 < Math.ceil(filteredData.length / dashboardState.tableFilters.rowsPerPage)) {{
                            dashboardState.tableFilters.pageIndex += 1;
                            renderTable();
                        }}
                    }};
                    paginationControls.appendChild(nextButton);

                    tableWrapper.appendChild(paginationControls);
                    container.appendChild(tableWrapper);
                }}

                // Helper function to apply table filters and sorting
                function applyTableFilters(data) {{
                    let filteredData = data;

                    // Apply sorting
                    if (dashboardState.tableFilters.sortColumn) {{
                        const column = dashboardState.tableFilters.sortColumn;
                        const direction = dashboardState.tableFilters.sortDirection;

                        filteredData.sort((a, b) => {{
                            let valueA = a[column];
                            let valueB = b[column];

                            if (!isNaN(valueA) && !isNaN(valueB)) {{
                                valueA = parseFloat(valueA);
                                valueB = parseFloat(valueB);
                            }} else {{
                                valueA = String(valueA).toLowerCase();
                                valueB = String(valueB).toLowerCase();
                            }}

                            return direction === 'asc' ? (valueA > valueB ? 1 : -1) : (valueA < valueB ? 1 : -1);
                        }});
                    }}

                    return filteredData;
                }}

                // Initialize the dashboard
                document.addEventListener('DOMContentLoaded', () => {{
                    renderCharts();
                    renderTable();
                }});
            </script>
        </body>
        </html>
        """

        # Save the HTML to a deployment directory
        deployment_directory = os.path.join(os.getcwd(), 'deployments')
        if not os.path.exists(deployment_directory):
            os.makedirs(deployment_directory)

        file_name = f"dashboard_{request.user.id}_{name.replace(' ', '_')}.html"
        file_path = os.path.join(deployment_directory, file_name)

        with open(file_path, 'w') as file:
            file.write(html_content)

        # Construct the deployed URL
        deployed_url = f"{request.build_absolute_uri('/')[:-1]}/deployments/{file_name}"

        # Update the dashboard with deployment information if needed
        dashboard.deployed_url = deployed_url
        dashboard.save()

        return JsonResponse({
            'message': 'Dashboard deployed successfully',
            'deployed_url': deployed_url
        })
    except Dashboard.DoesNotExist:
        return JsonResponse({'error': 'Dashboard not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except ValidationError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
