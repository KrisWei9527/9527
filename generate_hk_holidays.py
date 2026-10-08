from datetime import date, timedelta
from pathlib import Path
from korean_lunar_calendar import KoreanLunarCalendar
from collections import defaultdict

OUT = Path("hk-holidays-cn.ics")

# 🇭🇰 港股交易日历（中文）
# HKEX 香港证券市场：未来11年自动生成。
# 香港与中国大陆同为 UTC+8。
# 全日市：09:30-16:00
# 半日市：09:30-12:00
#
# 特别说明：
# - 周六、周日天然休市，不重复写入日历。
# - 公休日落在星期日时，按香港公休日规则顺延。
# - 临时休市、恶劣天气安排等特殊情况需以 HKEX 最新公告为准。

def lunar_to_solar(year, month, day):
    cal = KoreanLunarCalendar()
    if not cal.setLunarDate(year, month, day, False):
        raise ValueError(f"无法转换农历日期: {year}-{month}-{day}")
    return date.fromisoformat(cal.SolarIsoFormat())

def qingming(year):
    # 2000-2099 年清明节日期公式。
    y = year - 2000
    day = int(y * 0.2422 + 4.81) - int(y / 4)
    return date(year, 4, day)

def easter_sunday(year):
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19*a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2*e + 2*i - h - k) % 7
    m = (a + 11*h + 22*l) // 451
    month = (h + l - 7*m + 114) // 31
    day = ((h + l - 7*m + 114) % 31) + 1
    return date(year, month, day)

def add(items, d, name, kind="closed"):
    items.append({"date": d, "name": name, "kind": kind})

def base_holidays(year):
    items = []

    # 公历节日
    add(items, date(year, 1, 1), "元旦")
    add(items, date(year, 5, 1), "劳动节")
    add(items, date(year, 7, 1), "香港特别行政区成立纪念日")
    add(items, date(year, 10, 1), "国庆节")
    add(items, date(year, 12, 25), "圣诞节")

    # 清明
    add(items, qingming(year), "清明节")

    # 复活节相关
    easter = easter_sunday(year)
    add(items, easter - timedelta(days=2), "耶稣受难日")
    add(items, easter - timedelta(days=1), "耶稣受难日次日")
    add(items, easter + timedelta(days=1), "复活节星期一")

    # 农历节日
    add(items, lunar_to_solar(year, 4, 8), "佛诞")
    add(items, lunar_to_solar(year, 5, 5), "端午节")

    mid = lunar_to_solar(year, 8, 15)
    add(items, mid + timedelta(days=1), "中秋节翌日")

    add(items, lunar_to_solar(year, 9, 9), "重阳节")

    cny = lunar_to_solar(year, 1, 1)
    add(items, cny, "农历新年初一")
    add(items, cny + timedelta(days=1), "农历新年初二")
    add(items, cny + timedelta(days=2), "农历新年初三")

    # 半日市：农历新年前夕、圣诞节前夕、元旦前夕
    for d, name in [
        (cny - timedelta(days=1), "农历新年除夕"),
        (date(year, 12, 24), "圣诞节前夕"),
        (date(year, 12, 31), "元旦前夕"),
    ]:
        if d.weekday() < 5:
            add(items, d, name, "half")

    return items

def apply_hk_substitution(items):
    # 香港公休日如落在星期日，翌日为公休日。
    # 若翌日同时已有另一公休日，两个原因合并显示；
    # 该翌日公休日仍可继续产生再下一日的“翌日”公休日。
    result = list(items)

    for x in list(items):
        d = x["date"]
        if x["kind"] == "closed" and d.weekday() == 6:
            result.append({
                "date": d + timedelta(days=1),
                "name": x["name"] + "翌日",
                "kind": "closed",
            })

    # 周末本身不重复显示；同一天多个休市原因合并成一个事件。
    grouped = defaultdict(list)
    for x in result:
        if x["kind"] == "closed" and x["date"].weekday() >= 5:
            continue
        grouped[(x["date"], x["kind"])].append(x["name"])

    final = []
    for (d, kind), names in sorted(grouped.items()):
        # 若全日休市与半日市同日，以全日休市为准。
        if kind == "half" and (d, "closed") in grouped:
            continue
        # 保持顺序并去重
        unique_names = list(dict.fromkeys(names))
        final.append({"date": d, "kind": kind, "name": "＋".join(unique_names)})
    return final

today = date.today()
start_year = today.year
end_year = start_year + 10

lines = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//KrisWei9527//HKEX港股交易日历 中文版//CN",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
    "X-WR-CALNAME:🇭🇰 港股交易日历（中文）",
    "X-WR-CALDESC:HKEX香港证券市场休市及半日市日历；香港/CN 09:30-16:00，全日；09:30-12:00，半日。",
]

for year in range(start_year, end_year + 1):
    for x in apply_hk_substitution(base_holidays(year)):
        d = x["date"]
        if x["kind"] == "closed":
            summary = f"{x['name']}休市 🇭🇰"
            desc = "HKEX港股｜香港 09:30-16:00｜CN 09:30-16:00"
        else:
            summary = f"{x['name']}半日市｛HK 09:30-12:00/CN 09:30-12:00｝"
            desc = "HKEX港股半日市｜香港/CN 09:30-12:00"

        uid = f"hkex-stock-{d:%Y%m%d}-{x['kind']}-{x['name']}@KrisWei9527"
        lines += [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{today:%Y%m%d}T000000Z",
            f"DTSTART;VALUE=DATE:{d:%Y%m%d}",
            f"DTEND;VALUE=DATE:{(d + timedelta(days=1)):%Y%m%d}",
            f"SUMMARY:{summary}",
            f"DESCRIPTION:{desc}",
            "TRANSP:TRANSPARENT",
            "END:VEVENT",
        ]

lines.append("END:VCALENDAR")
OUT.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")
print(f"Generated {OUT} for {start_year}-{end_year}")
