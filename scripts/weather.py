#!/usr/bin/env python3
"""中央气象台(nmc.cn)天气查询。用法: python3 weather.py [城市名]"""
import sys, json, requests

BASE = "https://www.nmc.cn/rest"
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def get(path, **params):
    r = requests.get(f"{BASE}{path}", params=params, headers=H, timeout=20)
    r.raise_for_status()
    return r.json()


def find_city(name):
    """省 code → 城市 code。先匹配省级，未命中则全扫 34 省城市列表。"""
    provs = get("/province/all")
    for p in provs:
        if name in p["name"]:
            cities = get(f"/province/{p['code']}")
            for c in cities:
                if name in c["city"]:
                    return c
    print(f"[~] 省级未匹配「{name}」，正在扫描全部 34 省城市列表…")
    for p in provs:
        try:
            cities = get(f"/province/{p['code']}")
        except Exception:
            continue
        for c in cities:
            if name in c["city"]:
                return c
    return None


def fmt_w(w):
    return w["info"] if w["info"] not in ("9999", "") else "--"


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "北京"
    city = find_city(name)
    if not city:
        print(f"[!] 未找到城市: {name}")
        sys.exit(1)

    d = get("/weather", stationid=city["code"])["data"]
    real, predict, air = d["real"], d["predict"], d.get("air", {})

    rw = real["weather"]
    print(f"\n[{city['city']}] 实况 ({real['publish_time']} 发布)")
    print(f"  天气: {fmt_w(rw)}  {rw['temperature']}℃  体感 {rw['feelst']}℃")
    wind = real["wind"]
    print(f"  湿度: {rw['humidity']}%  {wind['direct']} {wind['power']}  降水 {rw['rain']}mm")
    warn = real["warn"]
    if warn.get("alert") and warn["alert"] != "9999":
        print(f"  ⚠️ {warn['alert']}")

    print(f"\n预报 ({predict['publish_time']} 发布)")
    for item in predict["detail"][:7]:
        day, night = item["day"], item["night"]
        d_ = fmt_w(day["weather"]), fmt_w(night["weather"])
        t_ = day["weather"]["temperature"], night["weather"]["temperature"]
        line = f"  {item['date'][5:]}: 白天 {d_[0]} {t_[0]}℃ / 夜间 {d_[1]} {t_[1]}℃"
        if item.get("precipitation") not in (None, "9999"):
            line += f"  降水 {item['precipitation']}mm"
        print(line)

    if air and air.get("aqi"):
        print(f"\n空气质量: AQI {air['aqi']} {air.get('text','')} ({air.get('forecasttime','')} 更新)")
    print()


if __name__ == "__main__":
    main()
