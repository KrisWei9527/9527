from datetime import date, timedelta
from pathlib import Path
from korean_lunar_calendar import KoreanLunarCalendar
OUT = Path("kr-holidays-cn.ics")
# 韩国法定公休日（中文），每次生成未来11年。
# 依据韩国现行《관공서의 공휴일에 관한 규정》：
# 2026年起劳动节（5月1日）和宪法纪念日（7月17日）纳入公休日。
# 代替公休日按韩国现行规则计算；政府临时指定的临时公休日、
# 选举日等无法提前固定的日期不在自动计算范围内。

def lunar_to_solar(year, month, day):
    cal = KoreanLunarCalendar()
    if not cal.setLunarDate(year, month, day, False):
        raise ValueError(f"无法转换农历日期: {year}-{month}-{day}")
    return date.fromisoformat(cal.SolarIsoFormat())

def lunar_new_year(year):
    return lunar_to_solar(year, 1, 1)

def add_holiday(items, d, name, substitute_allowed=False):
    items.append({"date": d, "name": name, "sub": substitute_allowed})

def base_holidays(year):
    items = []

    # 固定日期公休日
    add_holiday(items, date(year, 1, 1), "元旦", False)
    add_holiday(items, date(year, 3, 1), "三一节（独立运动纪念日）", True)
    add_holiday(items, date(year, 5, 1), "劳动节", True)
    add_holiday(items, date(year, 5, 5), "儿童节", True)
    add_holiday(items, date(year, 6, 6), "显忠日", False)
    add_holiday(items, date(year, 7, 17), "宪法纪念日", True)
    add_holiday(items, date(year, 8, 15), "光复节", True)
    add_holiday(items, date(year, 10, 3), "开天节", True)
    add_holiday(items, date(year, 10, 9), "韩文日", True)
    add_holiday(items, date(year, 12, 25), "圣诞节", True)

    # 春节：农历除夕、正月初一、初二
    ny = lunar_new_year(year)
    add_holiday(items, ny - timedelta(days=1), "春节（除夕）", True)
    add_holiday(items, ny, "春节", True)
    add_holiday(items, ny + timedelta(days=1), "春节（初二）", True)

    # 佛诞：农历四月初八
    add_holiday(items, lunar_to_solar(year, 4, 8), "佛诞日", True)

    # 中秋：农历八月十四、十五、十六
    for day, label in [(14, "中秋节前日"), (15, "中秋节"), (16, "中秋节次日")]:
        add_holiday(items, lunar_to_solar(year, 8, day), label, True)

    return items

def observed_dates(items):
    # 韩国现行规则：
    # 允许代替公休日的节日如遇周末，或与其他公休日重合，
    # 顺延至之后第一个非公休日；春节/中秋在周日重合时也适用。
    holidays = {x["date"] for x in items}
    result = [(x["date"], x["name"], False) for x in items]

    for x in items:
        d = x["date"]
        need = False

        if x["sub"] and d.weekday() in (5, 6):
            # 周六/周日
            need = True
        elif x["sub"] and d.weekday() < 5 and d + timedelta(days=0) in holidays:
            # 同一天重合由下方统一处理；此分支保留结构
            pass

        # 与另一个公休日重合（同一天有不同公休日）
        same_day = [y for y in items if y["date"] == d]
        if x["sub"] and len(same_day) > 1:
            need = True

        if need:
            candidate = d + timedelta(days=1)
            while candidate in holidays:
                candidate += timedelta(days=1)
            result.append((candidate, f"{x['name']}（代替公休日）", True))
            holidays.add(candidate)

    # 防止同一天重复显示同一事件
    seen = set()
    final = []
    for d, name, is_sub in sorted(result, key=lambda z: (z[0], z[1])):
        key = (d, name)
        if key not in seen:
            final.append((d, name, is_sub))
            seen.add(key)
    return final

today = date.today()
start_year = today.year
end_year = start_year + 10

lines = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//KrisWei9527//韩国公休日 中文版//CN",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
    "X-WR-CALNAME:韩国公休日（中文）",
    "X-WR-CALDESC:韩国法定公休日及依法计算的代替公休日（中文）",
]

for year in range(start_year, end_year + 1):
    for d, name, is_sub in observed_dates(base_holidays(year)):
        uid = f"kr-holiday-{d:%Y%m%d}-{name}@KrisWei9527"
        lines += [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{today:%Y%m%d}T000000Z",
            f"DTSTART;VALUE=DATE:{d:%Y%m%d}",
            f"DTEND;VALUE=DATE:{(d + timedelta(days=1)):%Y%m%d}",
            f"SUMMARY:{name}",
            "TRANSP:TRANSPARENT",
            "END:VEVENT",
        ]

lines.append("END:VCALENDAR")
OUT.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")
print(f"Generated {OUT} for {start_year}-{end_year}")
