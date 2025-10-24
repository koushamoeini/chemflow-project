from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseForbidden
from core.utils import require_password
from .models import OvertimeRequest, OvertimeStatus
from .forms import OvertimeRequestForm, OvertimeItemFormSet

@login_required
def my_tasks(request):
    role = getattr(getattr(request.user, "profile", None), "user_type", None)

    if role == "administrative_officer":
        return redirect("overtime:overtime_queue", queue_type='admin')
    
    if role == "factory_manager":
        return redirect("overtime:overtime_queue", queue_type='factory')
    
    if role == "management":
        return redirect("overtime:overtime_queue", queue_type='admin')

    messages.info(request, "هیچ وظیفه معلقی برای نقش شما تعریف نشده است.")
    return redirect("overtime:overtime_list")

@login_required
def overtime_queue(request, queue_type):
    role = getattr(getattr(request.user, "profile", None), "user_type", None)
    queue_map = {
        'admin': {
            'allowed_roles': ["administrative_officer", "management"],
            'status': OvertimeStatus.ADMIN_PENDING,
            'title': "در انتظار تایید مسئول اداری"
        },
        'factory': {
            'allowed_roles': ["factory_manager", "management"],
            'status': OvertimeStatus.FACTORY_PENDING,
            'title': "در انتظار تایید مدیر کارخانه"
        },
        'management': {
            'allowed_roles': ["management"],
            'status': OvertimeStatus.MANAGEMENT_PENDING,
            'title': "در انتظار تایید مدیریت"
        }
    }

    if queue_type not in queue_map:
        return HttpResponseForbidden("صف انتظار نامعتبر است.")

    config = queue_map[queue_type]
    if role not in config['allowed_roles']:
        return HttpResponseForbidden("شما دسترسی به این صف را ندارید.")

    requests_qs = OvertimeRequest.objects.filter(status=config['status']).select_related('created_by').prefetch_related('items').all()
    for req in requests_qs:
        req.user_can_edit = req.can_edit_or_cancel(request.user)

    context = {"requests": requests_qs, "title": config['title']}
    return render(request, "overtime/overtime_list.html", context)

@login_required
def overtime_list(request):
    role = getattr(getattr(request.user, "profile", None), "user_type", None)
    requests_qs = OvertimeRequest.objects.select_related('created_by').prefetch_related('items').all()
    for req in requests_qs:
        req.user_can_edit = req.can_edit_or_cancel(request.user)

    context = {
        'requests': requests_qs,
        'can_create': role in ["administrative_officer", "factory_manager", "management"],
        'role': role,
    }
    return render(request, 'overtime/overtime_list.html', context)

@login_required
def overtime_create(request):
    role = getattr(getattr(request.user, "profile", None), "user_type", None)
    allowed_roles = ["administrative_officer", "factory_manager", "management"]
    if role not in allowed_roles:
        messages.error(request, "اجازه ایجاد درخواست اضافه کاری ندارید.")
        return redirect('overtime:overtime_list')

    if request.method == 'POST':
        form = OvertimeRequestForm(request.POST)
        formset = OvertimeItemFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                overtime_request = form.save(commit=False)
                overtime_request.created_by = request.user
                overtime_request.status = OvertimeStatus.ADMIN_PENDING
                overtime_request.save()
                formset.instance = overtime_request
                formset.save()
            messages.success(request, "درخواست اضافه کاری با موفقیت ثبت و ارسال شد.")
            return redirect('overtime:overtime_detail', pk=overtime_request.pk)
    else:
        form = OvertimeRequestForm()
        formset = OvertimeItemFormSet()

    return render(request, 'overtime/overtime_form.html', {
        'form': form, 'formset': formset, 'title': 'ثبت درخواست اضافه کاری جدید'
    })

@login_required
def overtime_detail(request, pk):
    overtime_request = get_object_or_404(OvertimeRequest.objects.prefetch_related('items'), pk=pk)
    role = getattr(getattr(request.user, "profile", None), "user_type", None)

    context = {
        'object': overtime_request,
        'role': role,
        'can_approve': False,
        'can_edit': overtime_request.can_edit_or_cancel(request.user),
        'can_cancel': overtime_request.can_edit_or_cancel(request.user),
    }

    template_map = {
        'administrative_officer': 'overtime/details/administrative_officer_details.html',
        'factory_manager': 'overtime/details/factory_manager_details.html',
        'management': 'overtime/details/management_details.html',
    }
    template_name = template_map.get(role, 'overtime/details/read_only_details.html')

    if role == 'administrative_officer' and overtime_request.can_approve_admin(request.user):
        context['can_approve'] = True
    elif role == 'factory_manager' and overtime_request.can_approve_factory(request.user):
        context['can_approve'] = True
    elif role == 'management' and overtime_request.can_approve_management(request.user):
        context['can_approve'] = True

    return render(request, template_name, context)

@login_required
def overtime_update(request, pk):
    overtime_request = get_object_or_404(OvertimeRequest, pk=pk)
    if not overtime_request.can_edit_or_cancel(request.user):
        messages.error(request, "اجازه ویرایش این درخواست را ندارید.")
        return redirect('overtime:overtime_detail', pk=overtime_request.pk)

    if request.method == 'POST':
        form = OvertimeRequestForm(request.POST, instance=overtime_request)
        formset = OvertimeItemFormSet(request.POST, instance=overtime_request)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                form.save()
                formset.save()
            messages.success(request, "درخواست با موفقیت به‌روزرسانی شد.")
            return redirect('overtime:overtime_detail', pk=overtime_request.pk)
    else:
        form = OvertimeRequestForm(instance=overtime_request)
        formset = OvertimeItemFormSet(instance=overtime_request)

    return render(request, 'overtime/overtime_form.html', {
        'form': form, 'formset': formset, 'title': f'ویرایش درخواست {overtime_request.request_number}'
    })

@login_required
def overtime_cancel(request, pk):
    overtime_request = get_object_or_404(OvertimeRequest, pk=pk)
    if not overtime_request.can_edit_or_cancel(request.user):
        messages.error(request, "اجازه لغو این درخواست را ندارید.")
        return redirect("overtime:overtime_detail", pk=overtime_request.pk)

    if request.method == "POST":
        if not authenticate(username=request.user.username, password=request.POST.get("confirm_password", "")):
            messages.error(request, "برای لغو، وارد کردن رمز عبور صحیح الزامی است.")
            return redirect("overtime:overtime_detail", pk=overtime_request.pk)

        overtime_request.status = OvertimeStatus.REJECTED
        overtime_request.save()
        messages.success(request, "درخواست با موفقیت لغو شد.")
        return redirect("overtime:overtime_detail", pk=overtime_request.pk)

    return HttpResponseForbidden("درخواست نامعتبر است.")

@require_password
@login_required
def admin_approve(request, pk):
    overtime_request = get_object_or_404(OvertimeRequest, pk=pk)
    if not overtime_request.can_approve_admin(request.user):
        messages.error(request, "اجازه تأیید به عنوان مسئول اداری ندارید.")
        return redirect('overtime:overtime_detail', pk=overtime_request.pk)

    overtime_request.status = OvertimeStatus.FACTORY_PENDING
    overtime_request.admin_approved_by = request.user
    overtime_request.admin_approved_at = timezone.now()
    overtime_request.save()
    messages.success(request, "درخواست با موفقیت تأیید شد و به مدیر کارخانه ارسال گردید.")
    return redirect('overtime:overtime_list')

@require_password
@login_required
def factory_approve(request, pk):
    overtime_request = get_object_or_404(OvertimeRequest, pk=pk)
    if not overtime_request.can_approve_factory(request.user):
        messages.error(request, "اجازه تأیید به عنوان مدیر کارخانه ندارید.")
        return redirect('overtime:overtime_detail', pk=overtime_request.pk)

    overtime_request.status = OvertimeStatus.MANAGEMENT_PENDING
    overtime_request.factory_approved_by = request.user
    overtime_request.factory_approved_at = timezone.now()
    overtime_request.save()
    messages.success(request, "درخواست با موفقیت تأیید شد و به مدیریت ارسال گردید.")
    return redirect('overtime:overtime_list')

@require_password
@login_required
def management_approve(request, pk):
    overtime_request = get_object_or_404(OvertimeRequest, pk=pk)
    if not overtime_request.can_approve_management(request.user):
        messages.error(request, "اجازه تأیید به عنوان مدیریت ندارید.")
        return redirect('overtime:overtime_detail', pk=overtime_request.pk)

    overtime_request.status = OvertimeStatus.APPROVED
    overtime_request.management_approved_by = request.user
    overtime_request.management_approved_at = timezone.now()
    overtime_request.save()
    messages.success(request, "درخواست با موفقیت تأیید نهایی شد.")
    return redirect('overtime:overtime_list')