from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse, NoReverseMatch
from orders.models import CustomerOrder, OrderStatus
from overtime.models import OvertimeRequest
from requests.models import Request

@login_required
def dashboard(request):
    role = getattr(getattr(request.user, "profile", None), "user_type", None)
    role_map = {
        "management": ("مدیریت", "core/dashboards/management_dashboard.html"),
        "sales_manager": ("مدیر فروش", "core/dashboards/finance_dashboard.html"),
        "finance_manager": ("مدیر مالی", "core/dashboards/finance_dashboard.html"),
        "factory_planner": ("واحد برنامه‌ریزی", "core/dashboards/factory_planner_dashboard.html"),
        "factory_manager": ("مدیر کارخانه", "core/dashboards/factory_manager_dashboard.html"),
        "administrative_officer": ("مسئول اداری", "core/dashboards/administrative_officer_dashboard.html"),
    }
    
    role_fa, template_name = role_map.get(role, ("کاربر", "core/dashboards/read_only_dashboard.html"))

    counts = {
        "pending_sales": CustomerOrder.objects.filter(status=OrderStatus.DRAFT).count(),
        "pending_finance": CustomerOrder.objects.filter(status=OrderStatus.SALES_APPROVED).count(),
        "mine": CustomerOrder.objects.filter(created_by=request.user).count(),
    }
    
    return render(request, template_name, {"role": role, "counts": counts, "role_fa": role_fa})

def home(request):
    if request.user.is_authenticated:
        return redirect("core:dashboard")
    return render(request, "core/home.html")

@login_required
def my_all_requests(request):
    current_user = request.user
    combined_list = []

    overtime_reqs = OvertimeRequest.objects.filter(created_by=current_user)
    for req in overtime_reqs:
        combined_list.append({
            'type': 'اضافه کاری',
            'number': req.request_number,
            'status': req.get_status_display(),
            'date': req.created_at,
            'url': reverse('overtime:overtime_detail', args=[req.pk]),
            'can_edit': req.can_edit_or_cancel(current_user),
            'edit_url': reverse('overtime:overtime_update', args=[req.pk])
        })

    general_reqs = Request.objects.filter(created_by=current_user)
    for req in general_reqs:
        combined_list.append({
            'type': 'درخواست عمومی',
            'number': req.request_number,
            'status': req.get_status_display(),
            'date': req.created_at,
            'url': reverse('requests:request_detail', args=[req.pk]),
            'can_edit': req.can_edit_by(current_user),
            'edit_url': reverse('requests:request_update', args=[req.pk])
        })

    orders = CustomerOrder.objects.filter(created_by=current_user)
    for order in orders:
        try:
            can_edit_order = order.can_edit_by(current_user)
            edit_url_order = reverse('orders:order_update', args=[order.pk])
        except (AttributeError, NoReverseMatch):
            can_edit_order = False
            edit_url_order = ''
            
        combined_list.append({
            'type': 'سفارش فروش',
            'number': order.order_number,
            'status': order.get_status_display(),
            'date': order.created_at,
            'url': reverse('orders:order_details', args=[order.pk]),
            'can_edit': can_edit_order,
            'edit_url': edit_url_order
        })
        
    sorted_list = sorted(combined_list, key=lambda x: x['date'], reverse=True)

    context = {
        'requests': sorted_list,
        'title': 'لیست تمام درخواست‌های من'
    }
    
    return render(request, 'core/my_all_requests.html', context)