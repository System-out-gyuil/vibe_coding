from django import template
register = template.Library()

@register.filter
def get_field(entry, field):
    # 기본 필드 우선, 없으면 extra에서
    if hasattr(entry, field):
        val = getattr(entry, field)
        return val if val is not None else ''
    return entry.extra.get(field, '')

@register.filter
def get_item(data, key):
    return data.get(key, '')

@register.filter
def to_rgba(hex_color, alpha='0.18'):
    """HEX(#RRGGBB) -> rgba(r,g,b,a) 변환"""
    if not hex_color:
        return ''
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join([c*2 for c in hex_color])
    try:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f'rgba({r},{g},{b},{alpha})'
    except Exception:
        return '' 