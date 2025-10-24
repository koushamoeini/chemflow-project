from decimal import ROUND_HALF_EVEN
from django.db.models.query import resolve_callables
from core.utils import require_password
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction

from django.utils import timezone
from django.contrib.auth import authenticate

from .forms import RequestForm, RequestItemFormSet
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

    base_qs = Request.objects.exclude(status=RequestStatus.DRAFT).select_related("created_by").order_by("-id")

    if role in ["management", "factory_manager"]:
        requests_qs = base_qs
    else:
        requests_qs = base_qs.filter(created_by=request.user)

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
    if request.method == "POST":
        form = RequestForm(request.POST)
        formset = RequestItemFormSet(request.POST)

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
            else:
                messages.error(request, "فرم نامعتبر است. لطفاً خطاها را بررسی کنید.")
                return render(request, "requests/request_form.html", {"form": form, "formset": formset, "title": "ثبت درخواست جدید"})
        else:
             return render(request, "requests/request_form.html", {"form": form, "formset": formset, "title": "ثبت درخواست جدید"})


    else: # GET request
        form = RequestForm()
        formset = RequestItemFormSet()

    return render(request, "requests/request_form.html", {"form": form, "formset": formset, "title": "ثبت درخواست جدید"})


@login_required
def request_update(request, pk):
    request_obj = get_object_or_404(Request, pk=pk)

    if not request_obj.can_edit_by(request.user):
        messages.warning(request, "امکان ویرایش این درخواست برای شما وجود ندارد.")
        return redirect("requests:request_detail", pk=request_obj.pk)


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
            else:
                 messages.error(request, "لطفاً خطاهای فرم را برطرف کنید.")
                 return render(request, "requests/request_form.html", {"form": form, "formset": formset, "title": f"ویرایش {request_obj.request_number}"})
        else:
             return render(request, "requests/request_form.html", {"form": form, "formset": formset, "title": f"ویرایش {request_obj.request_number}"})


    else: # GET request
        form = RequestForm(instance=request_obj)
        formset = RequestItemFormSet(instance=request_obj)

    return render(request, "requests/request_form.html", {"form": form, "formset": formset, "title": f"ویرایش {request_obj.request_number}"})

@login_required
def request_detail(request, pk):
    request_obj = get_object_or_404(Request.objects.prefetch_related("items"), pk=pk)
    user = request.user
    role = _role(user)
    is_creator = request_obj.created_by == user

    can_approve_creator_flag = request_obj.can_approve_creator(user)
    can_approve_factory_flag = request_obj.can_approve_factory(user)
    can_approve_management_flag = request_obj.can_approve_management(user)

    creator_template = "requests/details/creator_request_details.html"
    factory_manager_template = "requests/details/factory_manager_request_details.html"
    management_template = "requests/details/management_request_details.html"
    read_only_template = "requests/details/read_only_request_details.html"

    template_name = read_only_template # Default

    if is_creator and can_approve_creator_flag:
        template_name = creator_template
    elif role == 'factory_manager' and can_approve_factory_flag:
        template_name = factory_manager_template
    elif role == 'management' and can_approve_management_flag:
        template_name = management_template
    elif role == 'factory_manager': # User has the role but cannot approve the current step
        template_name = factory_manager_template
    elif role == 'management': # User has the role but cannot approve the current step
        template_name = management_template
    elif is_creator: # Creator but cannot approve (already approved or wrong status)
         template_name = creator_template # Still show creator view, just without approve button


    context = {
        "request_obj": request_obj,
        "role": role,
        "is_creator": is_creator,
        "can_edit": request_obj.can_edit_by(user),
        "can_cancel": request_obj.can_cancel(user),
        "can_approve_creator": can_approve_creator_flag,
        "can_approve_factory": can_approve_factory_flag,
        "can_approve_management": can_approve_management_flag,
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
            messages.error(request, "برای لغو، وارد کردن رمز عبور صحیح الزامی است.")
            return redirect("requests:request_detail", pk=request_obj.pk)

        reason = request.POST.get("cancel_reason", "").strip()
        request_obj.status = RequestStatus.CANCELED
        request_obj.canceled_by = request.user
        request_obj.canceled_at = timezone.now()
        request_obj.cancel_reason = reason
        request_obj.save()
        messages.success(request, "درخواست با موفقیت لغو شد.")
        return redirect("requests:request_detail", pk=request_obj.pk)

    messages.error(request, "درخواست لغو نامعتبر است (باید POST باشد).")
    return redirect("requests:request_detail", pk=request_obj.pk)

