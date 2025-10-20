from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse, NoReverseMatch
from orders.models import CustomerOrder, OrderStatus
from overtime.models import OvertimeRequest, OvertimeStatus
from requests.models import Request, RequestStatus
from planning.models import ProductionRequest, ProductionStatus

# --- ایمپورت‌های جدید برای ویو "وظایف من" ---
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from requests.models import Request as GeneralRequest # تغییر نام برای جلوگیری از تداخل


@login_required
def dashboard(request):
    role = getattr(getattr(request.user, "profile", None), "user_type", None)
    role_map = {
        "management": ("مدیریت", "core/dashboards/management_dashboard.html"),
        "sales_manager": ("مدیر فروش", "core/dashboards/sales_dashboard.html"),
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
        "pending_admin_overtime": OvertimeRequest.objects.filter(status=OvertimeStatus.ADMIN_PENDING).count(),
        "pending_factory_production": ProductionRequest.objects.filter(status=ProductionStatus.PLANNING_SIGNED, factory_signed_by__isnull=True).count(),
        "pending_factory_overtime": OvertimeRequest.objects.filter(status=OvertimeStatus.FACTORY_PENDING).count(),
        "pending_factory_requests": Request.objects.filter(status=RequestStatus.CREATOR_APPROVED).count(),
        "pending_planning": ProductionRequest.objects.filter(status=ProductionStatus.DRAFT).count(),
    }
    
    return render(request, template_name, {"role": role, "counts": counts, "role_fa": role_fa})

    
def home(request):
    if request.user.is_authenticated:
        return redirect("core:dashboard")
    return render(request, "core/home.html")

@login_required
def my_all_requests(request):
    """
    این ویو، لیست تمام درخواست‌هایی که "من ایجاد کرده‌ام" را نشان می‌دهد.
    """
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
            # متد can_edit_by در مدل CustomerOrder شما وجود نداشت، من can_edit را استفاده می‌کنم
            # اگر متد شما can_edit_by است، این خط را اصلاح کنید
            can_edit_order = order.is_editable(current_user) 
            edit_url_order = reverse('orders:order_update', args=[order.pk])
        except (AttributeError, NoReverseMatch):
            can_edit_order = False
            edit_url_order = ''
            
        combined_list.append({
            'type': 'سفارش فروش',
            'number': order.order_number,
            'status': order.get_status_display(),
            'date': order.created_at,
            'url': reverse('orders:order_details', args=[order.pk]), # بر اساس کد شما اصلاح شد
            'can_edit': can_edit_order,
            'edit_url': edit_url_order
        })
        
    sorted_list = sorted(combined_list, key=lambda x: x['date'], reverse=True)

    context = {
        'requests': sorted_list,
        'title': 'لیست تمام درخواست‌های من'
    }
    
    return render(request, 'core/my_all_requests.html', context)


# --- کد جدید برای "وظایف من" (کارهایی که منتظر اقدام من است) ---

class MyTasksView(LoginRequiredMixin, ListView):
    """
    این ویو، لیست تمام وظایفی که "منتظر اقدام من" هستند را نشان می‌دهد.
    """
    template_name = 'core/my_all_tasks.html'  # این تمپلیت را باید بسازید
    context_object_name = 'tasks'
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        if not hasattr(user, 'profile'):
            return []

        role = user.profile.user_type
        all_tasks = []
        
        # --- ۱. وظایف فروش (Sales Tasks) ---
        sales_q = Q()
        if role in ['sales_manager', 'management']:
            sales_q |= Q(status=CustomerOrder.OrderStatus.DRAFT)
        if role in ['finance_manager', 'management']:
            sales_q |= Q(status=CustomerOrder.OrderStatus.SALES_APPROVED)
        if role == 'management':
            sales_q |= Q(status=CustomerOrder.OrderStatus.FINANCE_APPROVED)

        if sales_q:
            sales_tasks = CustomerOrder.objects.filter(sales_q)
            for task in sales_tasks:
                all_tasks.append({
                    'type': 'sales',
                    'type_display': 'فروش',
                    'title': f"سفارش {task.order_number}",
                    'status': task.get_status_display(),
                    'date': task.created_at,
                    # اصلاح شد بر اساس کد شما
                    'url': reverse('orders:order_details', args=[task.pk]) 
                })

        # --- ۲. وظایف اضافه‌کاری (Overtime Tasks) ---
        overtime_q = Q()
        if role == 'administrative_officer':
            overtime_q |= Q(status=OvertimeRequest.OvertimeStatus.ADMIN_PENDING)
        if role == 'factory_manager':
            overtime_q |= Q(status=OvertimeRequest.OvertimeStatus.FACTORY_PENDING)
        if role == 'management':
            overtime_q |= Q(status=OvertimeRequest.OvertimeStatus.MANAGEMENT_PENDING)

        if overtime_q:
            overtime_tasks = OvertimeRequest.objects.filter(overtime_q)
            for task in overtime_tasks:
                all_tasks.append({
                    'type': 'overtime',
                    'type_display': 'اضافه‌کاری',
                    'title': f"اضافه‌کاری {task.request_number}",
                    'status': task.get_status_display(),
                    'date': task.created_at,
                    'url': reverse('overtime:overtime_detail', args=[task.pk])
                })

        # --- ۳. وظایف تولید (Production Tasks) ---
        production_q = Q()
        if role in ['factory_planner', 'management']:
            production_q |= Q(status=ProductionRequest.ProductionStatus.DRAFT)
        if role in ['factory_manager', 'management']:
            production_q |= Q(status=ProductionRequest.ProductionStatus.PLANNING_SIGNED)

        if production_q:
            production_tasks = ProductionRequest.objects.filter(production_q)
            for task in production_tasks:
                all_tasks.append({
                    'type': 'production',
                    'type_display': 'تولید',
                    'title': f"تولید {task.request_number}",
                    'status': task.get_status_display(),
                    'date': task.created_at,
                    # این URL را چک کنید
                    'url': reverse('planning:production_detail', args=[task.pk])
                })

        # --- ۴. وظایف درخواست عمومی (General Requests) ---
        general_q = Q()
        general_q |= Q(created_by=user, status=GeneralRequest.RequestStatus.DRAFT) 
        if role == 'factory_manager':
            general_q |= Q(status=GeneralRequest.RequestStatus.CREATOR_APPROVED)
        if role == 'management':
            general_q |= Q(status=GeneralRequest.RequestStatus.FACTORY_APPROVED)

        if general_q:
            general_tasks = GeneralRequest.objects.filter(general_q)
            for task in general_tasks:
                all_tasks.append({
                    'type': 'general',
                    'type_display': 'درخواست عمومی',
                    'title': f"درخواست {task.request_number}",
                    'status': task.get_status_display(),
                    'date': task.created_at,
                    'url': reverse('requests:request_detail', args=[task.pk])
                })

        # --- فیلتر کردن بر اساس نوع ---
        filter_type = self.request.GET.get('type')
        if filter_type:
            all_tasks = [task for task in all_tasks if task['type'] == filter_type]

        # --- مرتب‌سازی نهایی بر اساس تاریخ (جدیدترین اول) ---
        all_tasks.sort(key=lambda x: x['date'], reverse=True)
        
        return all_tasks

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_filter'] = self.request.GET.get('type', '')
        return context