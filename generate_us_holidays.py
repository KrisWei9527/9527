from datetime import date, timedelta
from pathlib import Path

OUT = Path('us-holidays-cn.ics')

def nth_weekday(year, month, weekday, n):
    d = date(year, month, 1)
    return d + timedelta(days=(weekday - d.weekday()) % 7 + 7 * (n - 1))

def last_weekday(year, month, weekday):
    if month == 12:
        d = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        d = date(year, month + 1, 1) - timedelta(days=1)
    return d - timedelta(days=(d.weekday() - weekday) % 7)

def observed(d):
    if d.weekday() == 5: return d - timedelta(days=1)
    if d.weekday() == 6: return d + timedelta(days=1)
    return d

def holidays_for_year(y):
    return [
        (observed(date(y,1,1)), '元旦 🇺🇸'),
        (nth_weekday(y,1,0,3), '马丁·路德·金纪念日 🇺🇸'),
        (nth_weekday(y,2,0,3), '华盛顿诞辰日（总统日） 🇺🇸'),
        (last_weekday(y,5,0), '阵亡将士纪念日 🇺🇸'),
        (observed(date(y,6,19)), '六月节 🇺🇸'),
        (observed(date(y,7,4)), '独立日 🇺🇸'),
        (nth_weekday(y,9,0,1), '劳动节 🇺🇸'),
        (nth_weekday(y,10,0,2), '哥伦布日 🇺🇸'),
        (observed(date(y,11,11)), '退伍军人节 🇺🇸'),
        (nth_weekday(y,11,3,4), '感恩节 🇺🇸'),
        (observed(date(y,12,25)), '圣诞节 🇺🇸'),
    ]

today = date.today()
lines = [
    'BEGIN:VCALENDAR','VERSION:2.0',
    'PRODID:-//KrisWei9527//美国联邦节假日 中文版//CN',
    'CALSCALE:GREGORIAN','METHOD:PUBLISH',
    'X-WR-CALNAME:美国联邦节假日 🇺🇸（中文）',
]
for y in range(today.year, today.year + 11):
    for d, name in holidays_for_year(y):
        lines += ['BEGIN:VEVENT',
            f'UID:us-federal-{d:%Y%m%d}-{name}@KrisWei9527',
            f'DTSTAMP:{today:%Y%m%d}T000000Z',
            f'DTSTART;VALUE=DATE:{d:%Y%m%d}',
            f'DTEND;VALUE=DATE:{(d+timedelta(days=1)):%Y%m%d}',
            f'SUMMARY:{name}', 'TRANSP:TRANSPARENT', 'END:VEVENT']
lines.append('END:VCALENDAR')
OUT.write_text('\r\n'.join(lines)+'\r\n', encoding='utf-8')
