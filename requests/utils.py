from datetime import date
from .models import Request
from django.db.models import Max

def get_next_request_number():
    today = date.today()
    
    prefix = f"REQ-{today.strftime('%y%m')}-"
    
    max_number = Request.objects.filter(
        request_number__startswith=prefix
    ).aggregate(Max('request_number'))['request_number__max']

    if max_number:
        try:
            current_num = int(max_number.split('-')[-1])
            next_num = current_num + 1
        except ValueError:
            next_num = 1
    else:
        next_num = 1

    return f"{prefix}{next_num:04d}"