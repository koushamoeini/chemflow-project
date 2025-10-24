from core.utils import require_password
from django.http import HttpResponseForbidden
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from orders.models import CustomerOrder
from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from .models import PlanningStatus, ProductionRequest, ProductionStatus
from .forms import ProductionRequestForm, ProductionItemFormSet


@login_required
def ready_orders(request):
    role = _role(request.user)
    
    ready = CustomerOrder.objects.filter(
        sales_approved_by__isnull=False,
        finance_approved_by__isnull=False, 
        management_approved_by__isnull=False
    ).prefetch_related("items", "planning_status") 

    return render(request, "planning/ready_orders.html", {
        "orders": ready,
        "role": role
    })


def _role(user):
    return getattr(getattr(user, "profile", None), "user_type", None)


def _has_role(user, *roles):
    return _role(user) in roles


@login_required
def prodreq_list(request):
    role = getattr(getattr(request.user, "profile", None), "user_type", None)

    qs = ProductionRequest.objects.select_related("created_by").order_by("-id")

    if role in ["management", "factory_manager", "factory_planner"]:
        requests = qs
    else:
        requests = qs.none()

    ctx = {
        "requests": requests,
        "role": role,
        "can_create_prodreq": role in ["factory_planner", "management"],
        "is_management": role == "management",
        "is_factory_planner": role == "factory_planner",
        "is_factory_manager": role == "factory_manager",
    }
    return render(request, "planning/prodreq_list.html", ctx)


@login_required
def prodreq_create(request):
    if request.method == "POST":
        form = ProductionRequestForm(request.POST)
        formset = ProductionItemFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                req = form.save(commit=False)
                req.created_by = request.user
                req.save()
                formset.instance = req
                formset.save()
            messages.success(
                request,"درخواست تولید با موفقیت ثبت شد.")
            return redirect("planning:prodreq_detail", pk=req.pk)
        
        return render(request, "planning/prodreq_form.html", {"form": form, "formset": formset})

    form = ProductionRequestForm()
    formset = ProductionItemFormSet()
    return render(request, "planning/prodreq_form.html", {"form": form, "formset": formset})


@login_required
def prodreq_update(request, pk):
    req = get_object_or_404(ProductionRequest, pk=pk)
    if not req.can_edit_by(request.user):
        messages.error(request, "اجازه ویرایش ندارید.")
        return redirect("planning:prodreq_detail", pk=req.pk)

    if request.method == "POST":
        form = ProductionRequestForm(request.POST, instance=req)
        formset = ProductionItemFormSet(request.POST, instance=req)

        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                form.save()
                formset.save()
            messages.success(request, "درخواست به‌روزرسانی شد.")
            return redirect("planning:prodreq_detail", pk=req.pk)

        return render(request, "planning/prodreq_form.html", {"form": form, "formset": formset, "title": f"ویرایش {req.request_number}"})

    form = ProductionRequestForm(instance=req)
    formset = ProductionItemFormSet(instance=req)
    return render(request, "planning/prodreq_form.html", {"form": form, "formset": formset, "title": f"ویرایش {req.request_number}"})


@login_required
def prodreq_detail(request, pk):
    req = get_object_or_404(ProductionRequest.objects.prefetch_related("items"), pk=pk)
    role = _role(request.user)
    
    if role == "factory_planner":
        template_name = "planning/details/planner_prodreq_detail.html"
    elif role == "factory_manager":
        template_name = "planning/details/manager_prodreq_detail.html"
    else:
        template_name = "planning/details/prodreq_detail.html"
        
    ctx = {
        "req": req,
        "role": role,
        "can_edit": req.can_edit_by(request.user),
        "can_sign_planning": req.can_sign_planning(request.user),
        "can_sign_factory": req.can_sign_factory(request.user),
        "can_cancel": req.can_cancel(request.user),
    }
    return render(request, template_name, ctx)


@require_password
def sign_planning(request, pk):
    req = get_object_or_404(ProductionRequest, pk=pk)
    if not req.can_sign_planning(request.user):
        messages.error(
            request, "اجازه تأیید برنامه‌ریزی ندارید یا وضعیت مجاز نیست.")
        return redirect("planning:prodreq_detail", pk=req.pk)
    req.status = ProductionStatus.PLANNING_SIGNED
    req.planning_signed_by = request.user
    req.planning_signed_at = timezone.now()
    req.save()
    messages.success(request, "تأیید برنامه‌ریزی ثبت شد.")
    return redirect("planning:prodreq_detail", pk=req.pk)


@require_password
def sign_factory(request, pk):
    req = get_object_or_404(ProductionRequest, pk=pk)
    if not req.can_sign_factory(request.user):
        messages.error(
            request, "اجازه تأیید کارخانه ندارید یا وضعیت مجاز نیست.")
        return redirect("planning:prodreq_detail", pk=req.pk)
    req.status = ProductionStatus.FACTORY_SIGNED
    req.factory_signed_by = request.user
    req.factory_signed_at = timezone.now()
    req.save()
    messages.success(request, "تأیید کارخانه ثبت شد.")
    return redirect("planning:prodreq_detail", pk=req.pk)


@require_password
def cancel_prodreq(request, pk):
    req = get_object_or_404(ProductionRequest, pk=pk)

    if not req.can_cancel(request.user):
        messages.error(
            request, "شما اجازه لغو این درخواست را ندارید یا وضعیت درخواست مجاز نیست."
        )
        return redirect("planning:prodreq_detail", pk=req.pk)

    req.status = ProductionStatus.CANCELED
    req.canceled_by = request.user
    req.canceled_at = timezone.now()
    req.save()
    
    messages.success(request, "درخواست تولید با موفقیت لغو شد.")
    return redirect("planning:prodreq_detail", pk=req.pk)


@login_required
def my_tasks(request):
    role = _role(request.user)

    if role == "factory_planner":
        return redirect("planning:pending_planning")
    if role == "factory_manager":
        return redirect("planning:pending_factory")
    if role == "management":
        return redirect("planning:pending_planning")

    messages.info(request, "هیچ وظیفه معلقی برای نقش شما تعریف نشده است.")
    return redirect("core:dashboard")


@login_required
def pending_planning(request):
    role = _role(request.user)
    if role not in ["factory_planner", "management"]:
        return HttpResponseForbidden("دسترسی ندارند.")

    qs = ProductionRequest.objects.filter(status=ProductionStatus.DRAFT)
    return render(request, "planning/prodreq_list.html", {
        "requests": qs,
        "title": "در انتظار تأیید برنامه‌ریزی",
        "role": role,
        "can_create_prodreq": False,
        "is_management": role == "management",
        "is_factory_planner": role == "factory_planner",
        "is_factory_manager": role == "factory_manager"
    })


@login_required
def pending_factory(request):
    role = _role(request.user)
    if role not in ["factory_manager", "management"]:
        return HttpResponseForbidden("دسترسی ندارند.")

    qs = ProductionRequest.objects.filter(
        status=ProductionStatus.PLANNING_SIGNED,
        factory_signed_by__isnull=True
    )
    return render(request, "planning/prodreq_list.html", {
        "requests": qs,
        "title": "در انتظار تأیید کارخانه",
        "role": role,
        "can_create_prodreq": False,
        "is_management": role == "management",
        "is_factory_planner": role == "factory_planner",
        "is_factory_manager": role == "factory_manager"
    })
    
    
    
@login_required
def toggle_planning_status(request, pk):
    order = get_object_or_404(CustomerOrder, pk=pk)
    
    planning_status, created = PlanningStatus.objects.get_or_create(
        order=order,
        defaults={'is_planned': False, 'updated_by': request.user}
    )
    
    planning_status.is_planned = not planning_status.is_planned
    planning_status.updated_by = request.user
    planning_status.save()
    
    return redirect("planning:ready_orders")
