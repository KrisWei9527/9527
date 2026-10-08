from datetime import date, timedelta
from pathlib import Path

OUT = Path("us-holidays-cn.ics")

def nth_weekday(year, month, weekday, n):
    d = date(year, month, 1)
    return d + timedelta(days=(weekday - d.weekday()) % 7 + 7 * (n - 1))

def last_weekday(year, month, weekday):
    d = date(year + 1, 1, 1) - timedelta(days=1) if month == 12 else date(year, month + 1, 1) - timedelta(days=1)
    return d - timedelta(days=(d.weekday() - weekday) % 7)

def observed(d):
    if d.weekday() == 5:
        return d - timedelta(days=1)
    if d.weekday() == 6:
        return d + timedelta(days=1)
    return d

def easter_sunday(year):
    a=year%19; b=year//100; c=year%100; d=b//4; e=b%4; f=(b+8)//25; g=(b-f+1)//3
    h=(19*a+b-d-g+15)%30; i=c//4; k=c%4; l=(32+2*e+2*i-h-k)%7; m=(a+11*h+22*l)//451
    month=(h+l-7*m+114)//31
    day=((h+l-7*m+114)%31)+1
    return date(year, month, day)

def beijing_time_for_et_13(y, d):
    # 13:00 ET -> Beijing: next day 01:00 during U.S. DST,
    # next day 02:00 during U.S. standard time.
    # DST: second Sunday in March through first Sunday in November.
    dst_start = nth_weekday(y, 3, 6, 2)
    dst_end = nth_weekday(y, 11, 6, 1)
    if dst_start <= d < dst_end:
        return "北京时间次日01:00"
    return "北京时间次日02:00"

def holidays_for_year(y):
    closed = [
        (observed(date(y,1,1)), "元旦 🇺🇸"),
        (nth_weekday(y,1,0,3), "马丁·路德·金纪念日 🇺🇸"),
        (nth_weekday(y,2,0,3), "总统日 🇺🇸"),
        (easter_sunday(y)-timedelta(days=2), "耶稣受难日 🇺🇸"),
        (last_weekday(y,5,0), "阵亡将士纪念日 🇺🇸"),
        (observed(date(y,6,19)), "六月节 🇺🇸"),
        (observed(date(y,7,4)), "独立日 🇺🇸"),
        (nth_weekday(y,9,0,1), "劳动节 🇺🇸"),
        (nth_weekday(y,11,3,4), "感恩节 🇺🇸"),
        (observed(date(y,12,25)), "圣诞节 🇺🇸"),
    ]
    early = [
        (nth_weekday(y,11,3,4)+timedelta(days=1),
         "感恩节次日提前收盘（美东13:00 / 北京时间次日01:00或02:00） 🇺🇸")
    ]
    eve = date(y,12,24)
    if eve.weekday() < 5 and eve != observed(date(y,12,25)):
        early.append((eve, "圣诞节前夕提前收盘（美东13:00 / 北京时间次日01:00或02:00） 🇺🇸"))

    july4 = date(y,7,4)
    if july4.weekday() == 6:
        early.append((date(y,7,2), "独立日前夕提前收盘（美东13:00 / 北京时间次日01:00或02:00） 🇺🇸"))
    elif july4.weekday() in (1,2,3,4):
        early.append((date(y,7,3), "独立日前夕提前收盘（美东13:00 / 北京时间次日01:00或02:00） 🇺🇸"))
    return closed, early

today = date.today()
lines = [
    "BEGIN:VCALENDAR","VERSION:2.0",
    "PRODID:-//KrisWei9527//美股交易日历 中文版//CN",
    "CALSCALE:GREGORIAN","METHOD:PUBLISH",
    "X-WR-CALNAME:🇺🇸 美股交易日历（中文｜含北京时间）",
    "X-WR-TIMEZONE:Asia/Shanghai",
]
for y in range(today.year, today.year+11):
    closed, early = holidays_for_year(y)
    for d,name in closed:
        lines += [
            "BEGIN:VEVENT",
            f"UID:us-stock-closed-{d:%Y%m%d}@KrisWei9527",
            f"DTSTAMP:{today:%Y%m%d}T000000Z",
            f"DTSTART;VALUE=DATE:{d:%Y%m%d}",
            f"DTEND;VALUE=DATE:{(d+timedelta(days=1)):%Y%m%d}",
            f"SUMMARY:{name}",
            "DESCRIPTION:NYSE / Nasdaq 美股市场休市日。",
            "TRANSP:TRANSPARENT","END:VEVENT"
        ]
    for d,name in early:
        bj = beijing_time_for_et_13(y, d)
        name = name.replace("北京时间次日01:00或02:00", bj)
        lines += [
            "BEGIN:VEVENT",
            f"UID:us-stock-early-{d:%Y%m%d}@KrisWei9527",
            f"DTSTAMP:{today:%Y%m%d}T000000Z",
            f"DTSTART;VALUE=DATE:{d:%Y%m%d}",
            f"DTEND;VALUE=DATE:{(d+timedelta(days=1)):%Y%m%d}",
            f"SUMMARY:{name}",
            f"DESCRIPTION:NYSE / Nasdaq 美股提前收盘。美东时间13:00；{bj}。北京时间会因美国夏令时/冬令时变化。",
            "TRANSP:TRANSPARENT","END:VEVENT"
        ]
lines.append("END:VCALENDAR")
OUT.write_text("\r\n".join(lines)+"\r\n", encoding="utf-8")
