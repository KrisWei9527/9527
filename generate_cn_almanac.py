#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中国黄历 iCalendar 生成器
生成 2026-2036 年公历 + 农历 + 干支 + 生肖 + 宜忌 + 冲煞 + 节气/节日信息。
依赖：6tail/lunar-python
"""
from datetime import date, timedelta
from lunar_python import Solar

START_YEAR = 2026
END_YEAR = 2036
OUT = "cn-almanac.ics"

def esc(s):
    return str(s or "").replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")

def day_text(solar):
    lunar = solar.getLunar()
    parts = []

    # 农历、干支、生肖
    parts.append(f"农历：{lunar.getMonthInChinese()}月{lunar.getDayInChinese()}")
    parts.append(f"干支：{lunar.getYearInGanZhi()}年 {lunar.getMonthInGanZhi()}月 {lunar.getDayInGanZhi()}日")
    parts.append(f"生肖：{lunar.getYearShengXiao()}")

    # 黄历核心
    yi = lunar.getDayYi()
    ji = lunar.getDayJi()
    if yi:
        parts.append("宜：" + "、".join(yi))
    if ji:
        parts.append("忌：" + "、".join(ji))

    # 冲煞
    try:
        parts.append(f"冲煞：冲{lunar.getDayChongDesc()}；煞{lunar.getDaySha()}")
    except Exception:
        pass

    # 吉神凶煞
    try:
        shensha = lunar.getDayShenSha()
        if shensha:
            parts.append("神煞：" + "、".join(shensha))
    except Exception:
        pass

    # 节气/节日
    try:
        jq = lunar.getJieQi()
        if jq:
            parts.append("节气：" + str(jq))
    except Exception:
        pass

    try:
        festivals = lunar.getFestivals()
        if festivals:
            parts.append("节日：" + "、".join(festivals))
    except Exception:
        pass

    return "\\n".join(parts)

def main():
    events = []
    d = date(START_YEAR, 1, 1)
    end = date(END_YEAR + 1, 1, 1)

    while d < end:
        solar = Solar.fromYmd(d.year, d.month, d.day)
        summary = f"🇨🇳 {d.month}月{d.day}日 · {solar.getWeekInChinese()}"
        desc = day_text(solar)

        events.append(
            "BEGIN:VEVENT\r\n"
            f"UID:cn-almanac-{d.isoformat()}@KrisWei9527\r\n"
            f"DTSTART;VALUE=DATE:{d.strftime('%Y%m%d')}\r\n"
            f"DTEND;VALUE=DATE:{(d + timedelta(days=1)).strftime('%Y%m%d')}\r\n"
            f"SUMMARY:{esc(summary)}\r\n"
            f"DESCRIPTION:{esc(desc)}\r\n"
            "END:VEVENT\r\n"
        )
        d += timedelta(days=1)

    with open(OUT, "w", encoding="utf-8", newline="") as f:
        f.write("BEGIN:VCALENDAR\r\n")
        f.write("VERSION:2.0\r\n")
        f.write("PRODID:-//KrisWei9527//CN Chinese Almanac//CN\r\n")
        f.write("CALSCALE:GREGORIAN\r\n")
        f.write("METHOD:PUBLISH\r\n")
        f.write("X-WR-CALNAME:🇨🇳 中国黄历（农历·宜忌）\r\n")
        f.write("X-WR-TIMEZONE:Asia/Shanghai\r\n")
        f.write("X-WR-CALDESC:中国黄历：农历、干支、生肖、宜忌、冲煞、神煞、节气与传统节日\r\n")
        for e in events:
            f.write(e)
        f.write("END:VCALENDAR\r\n")

if __name__ == "__main__":
    main()
