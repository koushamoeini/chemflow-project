from decimal import ROUND_HALF_EVEN
from django.db.models.query import resolve_callables
from orders.utils import require_password
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.forms import inlineformset_factory
from django.utils import timezone
from django.contrib.auth import authenticate
from .forms import RequestForm, RequestItemForm
from .models import Request, RequestItem, RequestStatus
from .utils import get_next_request_number

def _role(user):
    return getattr(getattr(user, "profile", None), "user_type", None)

@login_required
def my_tasks(request):
    role = _role(request.user)

    if role == "factory_manager":
        return redirect("requests:request_queue", queue_type='factory')
    
    if role == "management":
        return redirect("requests:request_queue", queue_type='management')
    
    messages.info(request, "هیچ وظیفه معلقی برای نقش شما تعریف نشده است.")
    return redirect("requests:request_list")

@login_required
def request_queue(request, queue_type):
    role = _role(request.user)
    
    queue_map = {
        'factory': {
            'allowed_roles': ["factory_manager", "management"],
            'status': RequestStatus.CREATOR_APPROVED,
            'title': "در انتظار تایید مدیر کارخانه"
        },
        'management': {
            'allowed_roles': ["management"],
            'status': RequestStatus.FACTORY_APPROVED,
            'title': "در انتظار تایید مدیریت"
        }
    }

    if queue_type not in queue_map:
        return HttpResponseForbidden("صف انتظار نامعتبر است.")

    config = queue_map[queue_type]
    if role not in config['allowed_roles']:
        return HttpResponseForbidden("شما دسترسی به این صف را ندارید.")

    tasks_qs = Request.objects.filter(status=config['status'])
    
    # Check edit permission for each task
    for task in tasks_qs:
        task.user_can_edit = task.can_edit_by(request.user)
        
    context = {
        'requests': tasks_qs,
        'title': config['title']
    }
    return render(request, 'requests/request_list.html', context)

@login_required
def request_list(request):
    role = _role(request.user)

    base_qs = Request.objects.select_related("created_by").order_by("-id")

    if role in ["management", "factory_manager"]:
        requests_qs = base_qs
    else:
        requests_qs = base_qs.filter(created_by=request.user)

    # Check edit permission for each request
    for req in requests_qs:
        req.user_can_edit = req.can_edit_by(request.user)

    can_create = role in ["management"] or request.user.is_superuser

    return render(request, "requests/request_list.html", {
        "requests": requests_qs,
        "can_create": can_create,
        "title": "لیست درخواست‌ها"
    })

@login_required
def request_create(request):
    total_forms = 0
    if request.method == "POST" and "form-TOTAL_FORMS" in request.POST:
        try:
            total_forms = int(request.POST.get("form-TOTAL_FORMS", 0))
        except ValueError:
            total_forms = 0
    
    extra_rows = 1
    if "add_item" in request.POST:
        extra_rows = total_forms + 1

    DynamicRequestItemFormSet = inlineformset_factory(
        Request, 
        RequestItem,
        form=RequestItemForm, 
        extra=extra_rows, 
        can_delete=True, 
        min_num=1, 
        validate_min=True,
    )

    if request.method == "POST":
        form = RequestForm(request.POST)
        formset = DynamicRequestItemFormSet(request.POST)

        if "save_request" in request.POST:
            if form.is_valid() and formset.is_valid():
                with transaction.atomic():
                    new_request = form.save(commit=False)
                    new_request.created_by = request.user
                    new_request.request_number = get_next_request_number()
                    new_request.save()
                    
                    formset.instance = new_request
                    formset.save()
                
                messages.success(request, "درخواست با موفقیت ثبت شد.")
                return redirect("requests:request_detail", pk=new_request.pk)

            return render(request, "requests/request_form.html", {"form": form, "formset": formset, "title": "ثبت درخواست جدید"})
        
        return render(request, "requests/request_form.html", {"form": form, "formset": formset, "title": "ثبت درخواست جدید"})

    else:
        form = RequestForm()
        formset = DynamicRequestItemFormSet()

    return render(request, "requests/request_form.html", {"form": form, "formset": formset, "title": "ثبت درخواست جدید"})

@login_required
def request_update(request, pk):
    request_obj = get_object_or_404(Request, pk=pk)
    
    if not request_obj.can_edit_by(request.user):
        messages.warning(request, "امکان ویرایش این درخواست برای شما وجود ندارد.")
        return redirect("requests:request_detail", pk=request_obj.pk)
    
    RequestItemFormSet = inlineformset_factory(
        Request, RequestItem,
        form=RequestItemForm, extra=0,
        can_delete=True, min_num=1, validate_min=True
    )

    if request.method == "POST":
        form = RequestForm(request.POST, instance=request_obj)
        formset = RequestItemFormSet(request.POST, instance=request_obj)

        if "save_request" in request.POST:
            if form.is_valid() and formset.is_valid():
                with transaction.atomic():
                    form.save()
                    formset.save()
                messages.success(request, "درخواست با موفقیت به‌روزرسانی شد.")
                return redirect("requests:request_detail", pk=request_obj.pk)
            
            return render(request, "requests/request_form.html", {"form": form, "formset": formset, "title": f"ویرایش {request_obj.request_number}"})

    else:
        form = RequestForm(instance=request_obj)
        formset = RequestItemFormSet(instance=request_obj)

    return render(request, "requests/request_form.html", {"form": form, "formset": formset, "title": f"ویرایش {request_obj.request_number}"})

@login_required
def request_detail(request, pk):
    request_obj = get_object_or_404(Request.objects.prefetch_related("items"), pk=pk)
    role = _role(request.user)

    if request_obj.created_by == request.user:
        role = "creator"

    template_map = {
        "creator": "requests/details/creator_request_details.html",
        "factory_manager": "requests/details/factory_manager_request_details.html",
        "management": "requests/details/management_request_details.html",
    }
    template_name = template_map.get(role, "requests/details/read_only_request_details.html")

    context = {
        "request_obj": request_obj,
        "role": role,
        "can_edit": request_obj.can_edit_by(request.user),
        "can_cancel": request_obj.can_cancel(request.user),
        "can_approve_creator": request_obj.can_approve_creator(request.user),
        "can_approve_factory": request_obj.can_approve_factory(request.user),
        "can_approve_management": request_obj.can_approve_management(request.user),
    }

    return render(request, template_name, context)

@require_password
def approve_creator(request, pk):
    request_obj = get_object_or_404(Request, pk=pk)
    if not request_obj.can_approve_creator(request.user):
        messages.error(request, "اجازه تایید درخواست‌کننده را ندارید یا وضعیت فرم مجاز نیست.")
        return redirect("requests:request_detail", pk=request_obj.pk)
    request_obj.status = RequestStatus.CREATOR_APPROVED
    request_obj.creator_approved_by = request.user
    request_obj.creator_approved_at = timezone.now()
    request_obj.save()
    messages.success(request, "تایید درخواست‌کننده ثبت شد.")
    return redirect("requests:request_detail", pk=request_obj.pk)

@require_password
def approve_factory(request, pk):
    request_obj = get_object_or_404(Request, pk=pk)
    if not request_obj.can_approve_factory(request.user):
        messages.error(request, "اجازه تایید مدیر کارخانه را ندارید یا وضعیت فرم مجاز نیست.")
        return redirect("requests:request_detail", pk=request_obj.pk)
    request_obj.status = RequestStatus.FACTORY_APPROVED
    request_obj.factory_approved_by = request.user
    request_obj.factory_approved_at = timezone.now()
    request_obj.save()
    messages.success(request, "تایید مدیر کارخانه ثبت شد.")
    return redirect("requests:request_detail", pk=request_obj.pk)

@require_password
def approve_management(request, pk):
    request_obj = get_object_or_404(Request, pk=pk)
    if not request_obj.can_approve_management(request.user):
        messages.error(request, "اجازه تایید مدیر اصلی را ندارید یا وضعیت فرم مجاز نیست.")
        return redirect("requests:request_detail", pk=request_obj.pk)
    request_obj.status = RequestStatus.MANAGEMENT_APPROVED
    request_obj.management_approved_by = request.user
    request_obj.management_approved_at = timezone.now()
    request_obj.save()
    messages.success(request, "تایید مدیر اصلی ثبت شد.")
    return redirect("requests:request_detail", pk=request_obj.pk)

@login_required
def cancel_request(request, pk):
    request_obj = get_object_or_404(Request, pk=pk)
    if not request_obj.can_cancel(request.user):
        messages.error(request, "اجازه لغو این درخواست را ندارید.")
        return redirect("requests:request_detail", pk=request_obj.pk)

    if request.method == "POST":
        if not authenticate(username=request.user.username, password=request.POST.get("confirm_password", "")):
            messages.error(request, "برای لغو، وارد کردن رمز عبور الزامی است.")
            return redirect("requests:request_detail", pk=request_obj.pk)

        reason = request.POST.get("cancel_reason", "").strip()
        request_obj.status = RequestStatus.CANCELED
        request_obj.canceled_by = request.user
        request_obj.canceled_at = timezone.now()
        request_obj.cancel_reason = reason
        request_obj.save()
        messages.success(request, "درخواست با موفقیت لغو شد.")
        return redirect("requests:request_detail", pk=request_obj.pk)

    return HttpResponseForbidden("درخواست نامعتبر است.")