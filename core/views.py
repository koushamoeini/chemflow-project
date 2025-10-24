from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse, NoReverseMatch
from orders.models import CustomerOrder, OrderStatus
from overtime.models import OvertimeRequest, OvertimeStatus
from requests.models import Request as GeneralRequest, RequestStatus
from planning.models import ProductionRequest, ProductionStatus
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q


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

    total_tasks_count = 0
    
    sales_q = Q()
    if role == 'sales_manager':
        sales_q |= Q(status=OrderStatus.DRAFT)
    elif role == 'finance_manager':
        sales_q |= Q(status=OrderStatus.SALES_APPROVED)
    elif role == 'management':
        sales_q |= Q(status=OrderStatus.FINANCE_APPROVED)
    
    if sales_q:
        total_tasks_count += CustomerOrder.objects.filter(sales_q).count()

    overtime_q = Q()
    if role == 'administrative_officer':
        overtime_q |= Q(status=OvertimeStatus.ADMIN_PENDING)
    elif role == 'factory_manager':
        overtime_q |= Q(status=OvertimeStatus.FACTORY_PENDING)
    elif role == 'management':
        overtime_q |= Q(status=OvertimeStatus.MANAGEMENT_PENDING)
    
    if overtime_q:
        total_tasks_count += OvertimeRequest.objects.filter(overtime_q).count()

    production_q = Q()
    if role == 'factory_planner':
        production_q |= Q(status=ProductionStatus.DRAFT)
    elif role == 'factory_manager':
        production_q |= Q(status=ProductionStatus.PLANNING_SIGNED)
    elif role == 'management':
        pass
    
    if production_q:
        total_tasks_count += ProductionRequest.objects.filter(production_q).count()

    general_q = Q()
    if role == 'factory_manager':
        general_q |= Q(status=RequestStatus.CREATOR_APPROVED)
    elif role == 'management':
        general_q |= Q(status=RequestStatus.FACTORY_APPROVED)
    
    if general_q:
        total_tasks_count += GeneralRequest.objects.filter(general_q).distinct().count()
    
    counts = {
        "total_tasks_count": total_tasks_count,
        "pending_sales": CustomerOrder.objects.filter(status=OrderStatus.DRAFT).count(),
        "pending_finance": CustomerOrder.objects.filter(status=OrderStatus.SALES_APPROVED).count(),
        "mine": CustomerOrder.objects.filter(created_by=request.user).count(),
        "pending_admin_overtime": OvertimeRequest.objects.filter(status=OvertimeStatus.ADMIN_PENDING).count(),
        "pending_factory_production": ProductionRequest.objects.filter(status=ProductionStatus.PLANNING_SIGNED, factory_signed_by__isnull=True).count(),
        "pending_factory_overtime": OvertimeRequest.objects.filter(status=OvertimeStatus.FACTORY_PENDING).count(),
        "pending_factory_requests": GeneralRequest.objects.filter(status=RequestStatus.CREATOR_APPROVED).count(),
        "pending_planning": ProductionRequest.objects.filter(status=ProductionStatus.DRAFT).count(),
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
        try:
            edit_url = reverse('overtime:overtime_update', args=[req.pk]) if req.can_edit_or_cancel(current_user) else ''
            combined_list.append({
                'type': 'اضافه کاری',
                'number': req.request_number,
                'status': req.get_status_display(),
                'date': req.created_at,
                'url': reverse('overtime:overtime_detail', args=[req.pk]),
                'can_edit': req.can_edit_or_cancel(current_user),
                'edit_url': edit_url
            })
        except NoReverseMatch:
            pass # Handle cases where URL might not exist

    general_reqs = GeneralRequest.objects.filter(created_by=current_user)
    for req in general_reqs:
        try:
            edit_url = reverse('requests:request_update', args=[req.pk]) if req.can_edit_by(current_user) else ''
            combined_list.append({
                'type': 'درخواست عمومی',
                'number': req.request_number,
                'status': req.get_status_display(),
                'date': req.created_at,
                'url': reverse('requests:request_detail', args=[req.pk]),
                'can_edit': req.can_edit_by(current_user),
                'edit_url': edit_url
            })
        except NoReverseMatch:
            pass

    orders = CustomerOrder.objects.filter(created_by=current_user)
    for order in orders:
        try:
            can_edit_order = order.is_editable(current_user)
            edit_url_order = reverse('orders:order_update', args=[order.pk]) if can_edit_order else ''
            combined_list.append({
                'type': 'سفارش فروش',
                'number': order.order_number,
                'status': order.get_status_display(),
                'date': order.created_at,
                'url': reverse('orders:order_details', args=[order.pk]),
                'can_edit': can_edit_order,
                'edit_url': edit_url_order
            })
        except NoReverseMatch:
             pass

    # --- *** این بخش اضافه شد *** ---
    prod_reqs = ProductionRequest.objects.filter(created_by=current_user)
    for req in prod_reqs:
        try:
            can_edit_prod = req.can_edit_by(current_user)
            edit_url_prod = reverse('planning:prodreq_update', args=[req.pk]) if can_edit_prod else ''
            combined_list.append({
                'type': 'درخواست تولید',
                'number': req.request_number,
                'status': req.get_status_display(),
                'date': req.created_at,
                'url': reverse('planning:prodreq_detail', args=[req.pk]),
                'can_edit': can_edit_prod,
                'edit_url': edit_url_prod
            })
        except NoReverseMatch:
            pass
    # --- *** پایان بخش اضافه شده *** ---
            
    sorted_list = sorted(combined_list, key=lambda x: x['date'], reverse=True)

    context = {
        'requests': sorted_list,
        'title': 'لیست تمام درخواست‌های من'
    }
    
    return render(request, 'core/my_all_requests.html', context)


class MyTasksView(LoginRequiredMixin, ListView):
    template_name = 'core/my_all_tasks.html'
    context_object_name = 'tasks'
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        if not hasattr(user, 'profile'):
            return []

        role = user.profile.user_type
        all_tasks = []
        
        sales_q = Q()
        if role == 'sales_manager':
            sales_q |= Q(status=OrderStatus.DRAFT)
        elif role == 'finance_manager':
            sales_q |= Q(status=OrderStatus.SALES_APPROVED)
        elif role == 'management':
            sales_q |= Q(status=OrderStatus.FINANCE_APPROVED)

        if sales_q:
            sales_tasks = CustomerOrder.objects.filter(sales_q)
            for task in sales_tasks:
                try:
                    all_tasks.append({
                        'type': 'sales',
                        'type_display': 'فروش',
                        'title': f"سفارش {task.order_number}",
                        'status': task.get_status_display(),
                        'date': task.created_at,
                        'url': reverse('orders:order_details', args=[task.pk]) 
                    })
                except NoReverseMatch:
                    pass

        overtime_q = Q()
        if role == 'administrative_officer':
            overtime_q |= Q(status=OvertimeStatus.ADMIN_PENDING)
        elif role == 'factory_manager':
            overtime_q |= Q(status=OvertimeStatus.FACTORY_PENDING)
        elif role == 'management':
            overtime_q |= Q(status=OvertimeStatus.MANAGEMENT_PENDING)

        if overtime_q:
            overtime_tasks = OvertimeRequest.objects.filter(overtime_q)
            for task in overtime_tasks:
                try:
                    all_tasks.append({
                        'type': 'overtime',
                        'type_display': 'اضافه‌کاری',
                        'title': f"اضافه‌کاری {task.request_number}",
                        'status': task.get_status_display(),
                        'date': task.created_at,
                        'url': reverse('overtime:overtime_detail', args=[task.pk])
                    })
                except NoReverseMatch:
                    pass

        production_q = Q()
        if role == 'factory_planner':
            production_q |= Q(status=ProductionStatus.DRAFT)
        elif role == 'factory_manager':
            production_q |= Q(status=ProductionStatus.PLANNING_SIGNED)
        elif role == 'management':
            pass

        if production_q:
            production_tasks = ProductionRequest.objects.filter(production_q)
            for task in production_tasks:
                try:
                    all_tasks.append({
                        'type': 'production',
                        'type_display': 'تولید',
                        'title': f"تولید {task.request_number}",
                        'status': task.get_status_display(),
                        'date': task.created_at,
                        'url': reverse('planning:prodreq_detail', args=[task.pk])
                    })
                except NoReverseMatch:
                    pass

        general_q = Q()
        if role == 'factory_manager':
            general_q |= Q(status=RequestStatus.CREATOR_APPROVED)
        elif role == 'management':
            general_q |= Q(status=RequestStatus.FACTORY_APPROVED)

        if general_q:
            general_tasks = GeneralRequest.objects.filter(general_q).distinct()
            for task in general_tasks:
                try:
                    all_tasks.append({
                        'type': 'general',
                        'type_display': 'درخواست عمومی',
                        'title': f"درخواست {task.request_number}",
                        'status': task.get_status_display(),
                        'date': task.created_at,
                        'url': reverse('requests:request_detail', args=[task.pk])
                    })
                except NoReverseMatch:
                    pass

        filter_type = self.request.GET.get('type')
        if filter_type:
            all_tasks = [task for task in all_tasks if task['type'] == filter_type]

        all_tasks.sort(key=lambda x: x['date'], reverse=True)
        
        return all_tasks

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_filter'] = self.request.GET.get('type', '')
        
        user = self.request.user
        role = getattr(getattr(user, "profile", None), "user_type", None) # Safe access
        
        available_filters = {}

        # Use safe checks for role existence
        if role in ['sales_manager', 'finance_manager', 'management']:
            available_filters['sales'] = 'فروش'

        if role in ['factory_planner', 'factory_manager', 'management']: # Added management here if needed
            available_filters['production'] = 'تولید'

        if role in ['administrative_officer', 'factory_manager', 'management']:
            available_filters['overtime'] = 'اضافه‌کاری'
        
        if role in ['factory_manager', 'management']:
            available_filters['general'] = 'درخواست عمومی'
        
        context['available_filters'] = available_filters
        
        return context