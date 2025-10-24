from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth import authenticate
from django.db import transaction
from django.db.models import Q

from .forms import CustomerOrderForm, OrderItemFormSet
from .models import CustomerOrder, OrderStatus, Product, Customer
from core.utils import require_password

def _get_user_role(user):
    return getattr(getattr(user, "profile", None), "user_type", None)

@login_required
def order_list(request):
    role = _get_user_role(request.user)
    
    base_qs = CustomerOrder.objects.select_related("created_by").order_by("-id")

    if role in ["management", "sales_manager", "finance_manager"]:
        orders_list = base_qs.all()
    else:
        orders_list = base_qs.filter(created_by=request.user)
    
    for order in orders_list:
        order.user_can_edit = order.is_editable(request.user)

    context = {
        "orders": orders_list,
        "can_create": role in ["management", "sales_manager"],
        "title": "لیست تمام سفارش‌ها"
    }
    return render(request, "orders/order_list.html", context)


@login_required
def order_create(request):
    if request.method == "POST":
        form = CustomerOrderForm(request.POST, request=request)
        formset = OrderItemFormSet(request.POST, prefix='items')

        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                order = form.save(commit=False)
                order.created_by = request.user
                order.save()
                formset.instance = order
                formset.save()
            messages.success(request, "سفارش با موفقیت ثبت شد.")
            return redirect("orders:order_details", pk=order.pk)
    else:
        form = CustomerOrderForm(request=request)
        formset = OrderItemFormSet(prefix='items')

    context = {"form": form, "formset": formset, "title": "ثبت سفارش جدید"}
    return render(request, "orders/order_form.html", context)


@login_required
def order_update(request, pk):
    order = get_object_or_404(CustomerOrder, pk=pk)
    
    if not order.is_editable(request.user):
        messages.warning(request, "امکان ویرایش این سفارش برای شما وجود ندارد.")
        return redirect("orders:order_details", pk=order.pk)

    if request.method == "POST":
        form = CustomerOrderForm(request.POST, instance=order, request=request)
        formset = OrderItemFormSet(request.POST, instance=order, prefix='items')
        
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                form.save()
                formset.save()
            messages.success(request, "سفارش به‌روزرسانی شد.")
            return redirect("orders:order_details", pk=order.pk)
    else:
        form = CustomerOrderForm(instance=order, request=request)
        formset = OrderItemFormSet(instance=order, prefix='items')

    context = {"form": form, "formset": formset, "order": order, "title": f"ویرایش سفارش {order.order_number}"}
    return render(request, "orders/order_form.html", context)


@login_required
def order_detail(request, pk):
    order = get_object_or_404(CustomerOrder.objects.prefetch_related("items"), pk=pk)
    role = _get_user_role(request.user)
    
    template_map = {
        "sales_manager": "orders/details/sales_order_details.html",
        "finance_manager": "orders/details/finance_order_details.html",
        "management": "orders/details/management_order_details.html",
    }
    template_name = template_map.get(role, "orders/details/read_only_order_details.html")

    context = {
        "order": order,
        "role": role,
        "can_edit": order.is_editable(request.user),
        "can_approve_sales": order.can_approve_sales(request.user),
        "can_approve_finance": order.can_approve_finance(request.user),
        "can_approve_management": order.can_approve_management(request.user),
        "can_cancel": order.is_editable(request.user),
    }
    return render(request, template_name, context)


@require_password
def approve_order(request, pk, approval_type):
    order = get_object_or_404(CustomerOrder, pk=pk)
    
    approval_map = {
        'sales': {
            'permission_func': order.can_approve_sales,
            'new_status': OrderStatus.SALES_APPROVED,
            'user_field': 'sales_approved_by',
            'date_field': 'sales_approved_at',
            'message': 'تایید فروش ثبت شد.'
        },
        'finance': {
            'permission_func': order.can_approve_finance,
            'new_status': OrderStatus.FINANCE_APPROVED,
            'user_field': 'finance_approved_by',
            'date_field': 'finance_approved_at',
            'message': 'تایید مالی ثبت شد.'
        },
        'management': {
            'permission_func': order.can_approve_management,
            'new_status': OrderStatus.MANAGEMENT_APPROVED,
            'user_field': 'management_approved_by',
            'date_field': 'management_approved_at',
            'message': 'تایید مدیریت ثبت شد.'
        }
    }

    if approval_type not in approval_map:
        return HttpResponseForbidden("نوع تایید نامعتبر است.")

    config = approval_map[approval_type]
    
    if not config['permission_func'](request.user):
        messages.error(request, "شما اجازه انجام این کار را ندارید.")
        return redirect("orders:order_details", pk=order.pk)
        
    order.status = config['new_status']
    setattr(order, config['user_field'], request.user)
    setattr(order, config['date_field'], timezone.now())
    order.save()
    
    messages.success(request, config['message'])
    return redirect("orders:order_details", pk=order.pk)

@login_required
def pending_orders(request, queue_type):
    role = _get_user_role(request.user)
    
    queue_map = {
        'sales': {
            'allowed_roles': ["sales_manager", "management"],
            'status': OrderStatus.DRAFT,
            'title': "در انتظار تایید فروش"
        },
        'finance': {
            'allowed_roles': ["finance_manager", "management"],
            'status': OrderStatus.SALES_APPROVED,
            'title': "در انتظار تایید مالی"
        },
        'management': {
            'allowed_roles': ["management"],
            'status': OrderStatus.FINANCE_APPROVED,
            'title': "در انتظار تایید مدیریت"
        }
    }
    
    if queue_type not in queue_map:
        return HttpResponseForbidden("صف انتظار نامعتبر است.")
        
    config = queue_map[queue_type]
    
    if role not in config['allowed_roles']:
        return HttpResponseForbidden("شما دسترسی به این صف را ندارید.")
        
    orders_list = CustomerOrder.objects.filter(status=config['status']).select_related("created_by").order_by("-id")
    
    for order in orders_list:
        order.user_can_edit = order.is_editable(request.user)
        
    context = {"orders": orders_list, "title": config['title']}
    return render(request, "orders/order_list.html", context)


@login_required
def my_tasks(request):
    role = _get_user_role(request.user)
    
    role_map = {
        "sales_manager": "orders:pending_orders",
        "finance_manager": "orders:pending_orders",
        "management": "orders:pending_orders",
    }
    
    if role in role_map:
        queue_type = role.replace('_manager', '')
        return redirect(role_map[role], queue_type=queue_type)
        
    messages.info(request, "هیچ وظیفه معلقی برای نقش شما تعریف نشده است.")
    return redirect("core:dashboard")


@login_required
def cancel_order(request, pk):
    order = get_object_or_404(CustomerOrder, pk=pk)
    
    if not order.is_editable(request.user):
        messages.warning(request, "امکان لغو این سفارش برای شما وجود ندارد (چون قابل ویرایش نیست).")
        return redirect("orders:order_details", pk=order.pk)

    if request.method == "POST":
        if not authenticate(username=request.user.username, password=request.POST.get("confirm_password", "")):
            messages.error(request, "برای لغو، وارد کردن رمز عبور صحیح الزامی است.")
            return redirect("orders:order_details", pk=order.pk)

        reason = request.POST.get("cancel_reason", "").strip()
        order.status = OrderStatus.CANCELED
        order.canceled_by = request.user
        order.canceled_at = timezone.now()
        order.cancel_reason = reason
        order.save()
        messages.success(request, "سفارش با موفقیت لغو شد.")
        return redirect("orders:order_details", pk=order.pk)
    
    return HttpResponseForbidden("درخواست نامعتبر است.")


def customer_autocomplete(request):
    query = request.GET.get('q', '')
    customers = Customer.objects.filter(Q(name__icontains=query) | Q(customer_code__icontains=query))[:10] if query else Customer.objects.none()
    results = [{'id': c.id, 'name': c.name, 'phone': c.phone, 'address': c.address, 'code': c.customer_code} for c in customers]
    return JsonResponse(results, safe=False)

def product_autocomplete(request):
    query = request.GET.get('q', '')
    products = Product.objects.filter(Q(name__icontains=query) | Q(code__icontains=query))[:10] if query else Product.objects.none()
    results = [{'id': p.id, 'name': p.name, 'code': p.code} for p in products]
    return JsonResponse(results, safe=False)

