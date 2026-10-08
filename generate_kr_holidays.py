from datetime import date, timedelta
from pathlib import Path
from korean_lunar_calendar import KoreanLunarCalendar

OUT = Path("kr-holidays-cn.ics")

# 🇰🇷 韩国股市交易日历（KRX）
# 生成未来11年的 KOSPI/KOSDAQ 主要市场休市日。
# KRX 官方规则：周一至周五交易；公共假日、劳动节(5/1)、
# 年末最后交易日（通常为12/31；若该日为周末/公休日则提前至最近交易日）、
# 以及交易所临时指定的休市日不交易。
#
# 注意：临时公休日、选举日、KRX 临时决定的特殊休市日无法提前按固定规则推算。
# GitHub Actions 定期运行本脚本，可在韩国政府/证券交易所公布临时安排后及时补入规则。

def lunar_to_solar(year, month, day):
    cal = KoreanLunarCalendar()
    if not cal.setLunarDate(year, month, day, False):
        raise ValueError(f"无法转换农历日期: {year}-{month}-{day}")
    return date.fromisoformat(cal.SolarIsoFormat())

def lunar_new_year(year):
    return lunar_to_solar(year, 1, 1)

def add(items, d, name, substitute=False):
    items.append({"date": d, "name": name, "sub": substitute})

def public_holidays(year):
    items = []

    # 固定公休日
    add(items, date(year, 1, 1), "元旦", False)
    add(items, date(year, 3, 1), "三一节（独立运动纪念日）", True)
    add(items, date(year, 5, 1), "劳动节", True)  # KRX 明确休市
    add(items, date(year, 5, 5), "儿童节", True)
    add(items, date(year, 6, 6), "显忠日", False)
    add(items, date(year, 7, 17), "宪法纪念日", True)
    add(items, date(year, 8, 15), "光复节", True)
    add(items, date(year, 10, 3), "开天节", True)
    add(items, date(year, 10, 9), "韩文日", True)
    add(items, date(year, 12, 25), "圣诞节", True)

    # 春节：除夕、正月初一、初二
    ny = lunar_new_year(year)
    add(items, ny - timedelta(days=1), "春节（除夕）", True)
    add(items, ny, "春节", True)
    add(items, ny + timedelta(days=1), "春节（初二）", True)

    # 佛诞日：农历四月初八
    add(items, lunar_to_solar(year, 4, 8), "佛诞日", True)

    # 中秋：农历八月十四、十五、十六
    for day, label in [(14, "中秋节前日"), (15, "中秋节"), (16, "中秋节次日")]:
        add(items, lunar_to_solar(year, 8, day), label, True)

    return items

def substitute_dates(items):
    """按韩国代替公休日规则生成实际休市日。"""
    original_dates = {x["date"] for x in items}
    result = [(x["date"], x["name"], False) for x in items]

    for x in items:
        d = x["date"]
        need = False

        # 可代替公休日遇周六/周日
        if x["sub"] and d.weekday() in (5, 6):
            need = True

        # 可代替公休日与另一个公休日重合
        same_day_count = sum(1 for y in items if y["date"] == d)
        if x["sub"] and same_day_count > 1:
            need = True

        if need:
            candidate = d + timedelta(days=1)
            used = {r[0] for r in result}
            while candidate in original_dates or candidate in used:
                candidate += timedelta(days=1)
            result.append((candidate, f"{x['name']}（代替公休日）", True))

    # 去重
    seen = set()
    final = []
    for item in sorted(result, key=lambda z: (z[0], z[1])):
        if item[:2] not in seen:
            final.append(item)
            seen.add(item[:2])
    return final

def year_end_closure(year, holidays):
    """KRX 年末休市：12/31；若12/31为周末/公休日，则提前到最近交易日。"""
    d = date(year, 12, 31)
    if d.weekday() >= 5 or d in holidays:
        d -= timedelta(days=1)
        while d.weekday() >= 5 or d in holidays:
            d -= timedelta(days=1)
    return d

today = date.today()
start_year = today.year
end_year = start_year + 10

lines = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//KrisWei9527//KRX韩国股市交易日历 中文版//CN",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
    "X-WR-CALNAME:🇰🇷 韩国股市交易日历（中文）",
    "X-WR-CALDESC:韩国交易所 KRX/KOSPI/KOSDAQ 休市日历；韩国09:00-15:30，CN 08:00-14:30。",
]

for year in range(start_year, end_year + 1):
    items = substitute_dates(public_holidays(year))
    holiday_dates = {d for d, _, _ in items}

    # KRX 年末最后交易日休市
    year_end = year_end_closure(year, holiday_dates)
    if year_end not in holiday_dates:
        items.append((year_end, "年末休市", False))

    for d, name, is_sub in sorted(items, key=lambda z: (z[0], z[1])):
        uid = f"krx-stock-{d:%Y%m%d}-{name}@KrisWei9527"
        desc = f"KRX休市｜韩国 09:00-15:30｜CN 08:00-14:30"
        if name == "劳动节":
            desc += "｜KRX劳动节休市"
        if name == "年末休市":
            desc += "｜KRX年末最后交易日休市"
        if is_sub:
            desc += "｜代替公休日"
        lines += [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{today:%Y%m%d}T000000Z",
            f"DTSTART;VALUE=DATE:{d:%Y%m%d}",
            f"DTEND;VALUE=DATE:{(d + timedelta(days=1)):%Y%m%d}",
            f"SUMMARY:{name}休市 🇰🇷",
            f"DESCRIPTION:{desc}",
            "TRANSP:TRANSPARENT",
            "END:VEVENT",
        ]

lines.append("END:VCALENDAR")
OUT.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")
print(f"Generated {OUT} for {start_year}-{end_year}")
