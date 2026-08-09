#!/usr/bin/env python3
"""中央气象台(nmc.cn)天气查询。用法: python3 weather.py [城市名]"""
import sys, json, os, re, requests

BASE = "https://www.nmc.cn/rest"
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "city_cache.json")
SUFFIX = "市县区旗盟"


class AmbiguityError(Exception):
    """城市名有多个候选（重名），需要大模型追问用户确认。"""

    def __init__(self, name, cands):
        self.name, self.cands = name, cands


def base(n):
    return re.sub(rf"[{SUFFIX}]+$", "", n)


def load_cache():
    try:
        return json.load(open(CACHE))
    except Exception:
        return {}


def save_cache(cache):
    json.dump(cache, open(CACHE, "w"), ensure_ascii=False, indent=2)


def candidates(name, cities):
    """候选城市。带后缀=明确指定（唯一）；短名=所有基名相同（可能多个→歧义）。"""
    if name.endswith(tuple(SUFFIX)):
        exact = [c for c in cities if c["city"] == name]
        if exact:
            return exact
        b = base(name)
        return [c for c in cities if c["city"] == b]
    b = base(name)
    return [c for c in cities if base(c["city"]) == b]


def get(path, **params):
    r = requests.get(f"{BASE}{path}", params=params, headers=H, timeout=20)
    r.raise_for_status()
    return r.json()


def find_city(name):
    """省 code → 城市 code。先查本地缓存（城市 code 固定不变），miss 才请求接口并缓存。"""
    cache = load_cache()
    if name in cache:
        return cache[name]
    provs = get("/province/all")
    cities = []
    for p in provs:
        try:
            cities.extend(get(f"/province/{p['code']}"))
        except Exception:
            continue
    cands = candidates(name, cities)
    if len(cands) > 1:
        raise AmbiguityError(name, cands)
    if not cands:
        return None
    cache[name] = cands[0]
    save_cache(cache)
    return cands[0]


def fmt_w(w):
    return w["info"] if w["info"] not in ("9999", "") else "--"


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "北京"
    try:
        city = find_city(name)
    except AmbiguityError as e:
        print(f"[歧义] 「{e.name}」匹配到 {len(e.cands)} 个城市，请确认是哪一个：")
        for i, c in enumerate(e.cands, 1):
            print(f"  {i}. {c['province']} {c['city']}")
        print(f"请回答带省市的全称（如「北京朝阳」），再查询。")
        sys.exit(2)
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
