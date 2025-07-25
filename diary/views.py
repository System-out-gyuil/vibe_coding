from django.shortcuts import render
from .models import DiaryEntry, Category, Region, SalesStatus, BaseAttribute, Attribute, AttributeValue, User, DropdownAttribute, Row
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder
from django.views.decorators.http import require_GET, require_http_methods
import json
from django.db import models
import random

# 다이어리 목록 및 작성 폼

def diary_list(request):
    user = User.objects.get(id=1)
    attributes = BaseAttribute.objects.all().order_by('id')
    user_attributes = Attribute.objects.filter(user=user)
    attr_map = {attr.name: attr for attr in user_attributes}
    values = {}

    for attr in user_attributes:
        value_obj = AttributeValue.objects.filter(attribute=attr).first()
        values[attr.name] = value_obj.value if value_obj else ''

    return render(request, 'diary/diary_list.html', {
        'attributes': user_attributes,
        'values': values,
    })

@require_GET
def fu_events(request):
    events = []
    for entry in DiaryEntry.objects.exclude(fu_date=None):
        events.append({
            'id': entry.id,
            'title': entry.name,
            'start': entry.fu_date.strftime('%Y-%m-%d') if entry.fu_date else None,
            'meeting_date': entry.meeting_date.strftime('%Y/%m/%d') if entry.meeting_date else '',
            'status_name': entry.status.name if entry.status else '',
            'status_color': entry.status.color if entry.status and hasattr(entry.status, 'color') else '#bbb',
        })
    return JsonResponse(events, safe=False, encoder=DjangoJSONEncoder)

@csrf_exempt
@require_http_methods(["GET", "POST"])
def fu_memo(request, entry_id):
    try:
        entry = DiaryEntry.objects.get(id=entry_id)
    except DiaryEntry.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Not found'}, status=404)
    if request.method == 'GET':
        return JsonResponse({'success': True, 'memo': entry.memo or ''})
    elif request.method == 'POST':
        memo = request.POST.get('memo', '')
        entry.memo = memo
        entry.save()
        return JsonResponse({'success': True})

def random_color():
    return "#" + ''.join([random.choice('0123456789ABCDEF') for _ in range(6)])

@csrf_exempt
def category_list(request):
    if request.method == 'GET':
        return JsonResponse({'categories': list(Category.objects.values('id', 'name', 'color'))})
    elif request.method == 'POST':
        name = request.POST.get('name', '').strip()
        color = request.POST.get('color', '').strip()
        if name:
            if not color:
                color = random_color()
            cat, created = Category.objects.get_or_create(name=name, defaults={'color': color})
            if not created and not cat.color:
                cat.color = color
                cat.save()
            return JsonResponse({'id': cat.id, 'name': cat.name, 'color': cat.color, 'created': created})
        return JsonResponse({'error': 'No name'}, status=400)
    elif request.method == 'DELETE':
        id = request.GET.get('id')
        Category.objects.filter(id=id).delete()
        return JsonResponse({'success': True})
    elif request.method == 'PUT':
        id = request.GET.get('id')
        name = request.GET.get('name', '').strip()
        color = request.GET.get('color', '').strip()
        cat = Category.objects.filter(id=id).first()
        updated = False
        if cat:
            if name:
                cat.name = name
                updated = True
            if color:
                cat.color = color
                updated = True
            if updated:
                cat.save()
                return JsonResponse({'success': True})
        return JsonResponse({'error': 'Invalid'}, status=400)
    return JsonResponse({'error': 'Invalid method'}, status=405)

@csrf_exempt
def region_list(request):
    if request.method == 'GET':
        return JsonResponse({'regions': list(Region.objects.values('id', 'name'))})
    elif request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            reg, created = Region.objects.get_or_create(name=name)
            return JsonResponse({'id': reg.id, 'name': reg.name, 'created': created})
        return JsonResponse({'error': 'No name'}, status=400)
    elif request.method == 'DELETE':
        id = request.GET.get('id')
        Region.objects.filter(id=id).delete()
        return JsonResponse({'success': True})
    elif request.method == 'PUT':
        id = request.GET.get('id')
        name = request.GET.get('name', '').strip()
        reg = Region.objects.filter(id=id).first()
        if reg and name:
            reg.name = name
            reg.save()
            return JsonResponse({'success': True})
        return JsonResponse({'error': 'Invalid'}, status=400)
    return JsonResponse({'error': 'Invalid method'}, status=405)

@csrf_exempt
def create_entry(request):
    if request.method == 'POST':
        data = {field: request.POST.get(field, '') for field in [
            'name', 'subregion', 'address', 'manager', 'phone', 'email',
            'status', 'possibility', 'amount']}
        for date_field in ['ta_date', 'meeting_date', 'fu_date']:
            value = request.POST.get(date_field)
            data[date_field] = value if value else None
        cat_val = request.POST.get('category')
        reg_val = request.POST.get('region')
        status_val = request.POST.get('status')
        # category 처리
        if cat_val:
            if cat_val.isdigit():
                data['category'] = Category.objects.filter(id=cat_val).first()
            else:
                data['category'], _ = Category.objects.get_or_create(name=cat_val)
        else:
            data['category'] = None
        # region 처리
        if reg_val:
            if reg_val.isdigit():
                data['region'] = Region.objects.filter(id=reg_val).first()
            else:
                data['region'], _ = Region.objects.get_or_create(name=reg_val)
        else:
            data['region'] = None
        # status 처리 (추가)
        if status_val:
            if status_val.isdigit():
                data['status'] = SalesStatus.objects.filter(id=status_val).first()
            else:
                data['status'], _ = SalesStatus.objects.get_or_create(name=status_val)
        else:
            data['status'] = None
        # order 값 지정: 가장 큰 order+1
        max_order = DiaryEntry.objects.aggregate(max_order=models.Max('order'))['max_order']
        data['order'] = (max_order + 1) if max_order is not None else 0
        entry = DiaryEntry.objects.create(**data)
        return JsonResponse({'success': True, 'id': entry.id})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@csrf_exempt
def reorder_entries(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            ids = data.get('order', [])
            for idx, row_id in enumerate(ids):
                Row.objects.filter(id=row_id).update(order=idx)
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@csrf_exempt
def status_list(request):
    if request.method == 'GET':
        return JsonResponse({'statuses': list(SalesStatus.objects.values('id', 'name', 'color'))})
    elif request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            color = request.POST.get('color', '').strip()
            if not color:
                color = random_color()
            status, created = SalesStatus.objects.get_or_create(name=name, defaults={'color': color})
            if not created and not status.color:
                status.color = color
                status.save()
            return JsonResponse({'id': status.id, 'name': status.name, 'color': status.color, 'created': created})
        return JsonResponse({'error': 'No name'}, status=400)
    elif request.method == 'DELETE':
        id = request.GET.get('id')
        SalesStatus.objects.filter(id=id).delete()
        return JsonResponse({'success': True})
    elif request.method == 'PUT':
        id = request.GET.get('id')
        name = request.GET.get('name', '').strip()
        color = request.GET.get('color', '').strip()
        status = SalesStatus.objects.filter(id=id).first()
        if status:
            updated = False
            if name:
                status.name = name
                updated = True
            if color:
                status.color = color
                updated = True
            if updated:
                status.save()
                return JsonResponse({'success': True})
        return JsonResponse({'error': 'Invalid'}, status=400)
    return JsonResponse({'error': 'Invalid method'}, status=405)

def board_view(request):
    statuses = SalesStatus.objects.all().order_by('id')
    board = []
    for status in statuses:
        entries = DiaryEntry.objects.filter(status=status).order_by('order', 'id')
        board.append({'status': status, 'entries': entries})
    return render(request, 'diary/board.html', {'board': board, 'statuses': statuses})

@csrf_exempt
def update_entry(request):
    if request.method == 'POST':
        field = request.POST.get('field')
        value = request.POST.get('value')
        print(field, value)
        if not field:
            return JsonResponse({'success': False, 'error': 'Missing field'})
        user = User.objects.get(id=1)
        try:
            attr = Attribute.objects.get(name=field)
        except Attribute.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Invalid attribute'})
        attr_type = attr.attributeType.name if attr.attributeType else ''
        attribute, _ = Attribute.objects.get_or_create(
            name=attr.name,
            user=user,
            defaults={'attributeType': attr.attributeType}
        )
        # Dropdown 처리
        if attr_type == 'dropdown':
            dropdown, _ = DropdownAttribute.objects.get_or_create(
                attribute=attr,
                option=value
            )
            value_to_save = str(dropdown.id)
        else:
            value_to_save = value
        attr_value, created = AttributeValue.objects.get_or_create(
            attribute=attribute,
            defaults={'value': value_to_save}
        )
        if not created:
            attr_value.value = value_to_save
            attr_value.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid request'})