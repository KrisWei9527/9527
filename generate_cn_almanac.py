#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import date, timedelta
from lunar_python import Solar

START_YEAR = 2026
END_YEAR = 2036
OUT = "cn-almanac.ics"


def ics_text(text):
    """
    ICS 特殊字符处理。
    使用逗号和空格代替换行，避免 iPhone 显示 \\n。
    """
    if text is None:
        return ""

    return (
        str(text)
        .replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\r", " ")
        .replace("\n", " ")
    )


def make_description(solar):
    lunar = solar.getLunar()

    lines = []

    # 公历
    lines.append(f"📅 公历：{solar.toYmd()}")

    # 农历
    lines.append(
        f"🌙 农历：{lunar.getMonthInChinese()}月"
        f"{lunar.getDayInChinese()}"
    )

    # 年份和生肖
    try:
        lines.append(
            f"🐎 年份：{lunar.getYearInGanZhi()}年"
            f"（{lunar.getYearShengXiao()}年）"
        )
    except Exception:
        pass

    # 干支日
    try:
        lines.append(
            f"📅 干支日：{lunar.getDayInGanZhi()}日"
        )
    except Exception:
        pass

    # 宜
    try:
        yi = lunar.getDayYi()
        if yi:
            lines.append(
                "✅ 宜：" + "、".join(yi)
            )
    except Exception:
        pass

    # 忌
    try:
        ji = lunar.getDayJi()
        if ji:
            lines.append(
                "❌ 忌：" + "、".join(ji)
            )
    except Exception:
        pass

    # 冲煞
    try:
        lines.append(
            f"🔴 冲煞：冲{lunar.getDayChongDesc()}；"
            f"煞{lunar.getDaySha()}"
        )
    except Exception:
        pass

    # 节气
    try:
        jieqi = lunar.getJieQi()
        if jieqi:
            lines.append(
                f"🌿 节气：{jieqi}"
            )
    except Exception:
        pass

    # 节日
    try:
        festivals = lunar.getFestivals()
        if festivals:
            lines.append(
                "🎎 节日：" + "、".join(festivals)
            )
    except Exception:
        pass

    # iPhone 对 ICS DESCRIPTION 的兼容性考虑，
    # 使用全角空格分隔，避免显示 \n。
    return "　".join(lines)


def main():

    current = date(START_YEAR, 1, 1)
    end_date = date(END_YEAR + 1, 1, 1)

    events = []

    while current < end_date:

        solar = Solar.fromYmd(
            current.year,
            current.month,
            current.day
        )

        lunar = solar.getLunar()

        # 日历标题
        summary = (
            f"🇨🇳 农历 "
            f"{lunar.getMonthInChinese()}月"
            f"{lunar.getDayInChinese()} · "
            f"{lunar.getDayInGanZhi()}日"
        )

        description = make_description(solar)

        next_day = current + timedelta(days=1)

        event = (
            "BEGIN:VEVENT\r\n"
            f"UID:cn-almanac-{current.isoformat()}@KrisWei9527\r\n"
            f"DTSTART;VALUE=DATE:{current.strftime('%Y%m%d')}\r\n"
            f"DTEND;VALUE=DATE:{next_day.strftime('%Y%m%d')}\r\n"
            f"SUMMARY:{ics_text(summary)}\r\n"
            f"DESCRIPTION:{ics_text(description)}\r\n"
            "END:VEVENT\r\n"
        )

        events.append(event)

        current = next_day

    with open(
        OUT,
        "w",
        encoding="utf-8",
        newline=""
    ) as f:

        f.write("BEGIN:VCALENDAR\r\n")
        f.write("VERSION:2.0\r\n")
        f.write(
            "PRODID:-//KrisWei9527//"
            "CN Chinese Almanac//CN\r\n"
        )
        f.write("CALSCALE:GREGORIAN\r\n")
        f.write("METHOD:PUBLISH\r\n")

        # iPhone 日历名称
        f.write("X-WR-CALNAME:🇨🇳 黄历\r\n")

        f.write(
            "X-WR-TIMEZONE:Asia/Shanghai\r\n"
        )

        f.write(
            "X-WR-CALDESC:"
            "中国黄历：农历、生肖、干支、"
            "宜忌、冲煞、节气、传统节日\r\n"
        )

        for event in events:
            f.write(event)

        f.write("END:VCALENDAR\r\n")


if __name__ == "__main__":
    main()
