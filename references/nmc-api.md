# 中央气象台 nmc.cn 公开 JSON 接口文档

> 中国气象局官方数据源（中央气象台官网 www.nmc.cn）。免费、免注册、免 key。
> 实测日期：2026-08-03

## 接口列表

### 1. 省份列表

```
GET https://www.nmc.cn/rest/province/all
```

返回 34 个省级行政区：

```json
[{"code": "ABJ", "name": "北京市", "url": "/publish/forecast/ABJ.html"}, ...]
```

| 字段 | 说明 |
|:---|:---|
| code | 省 code（ABJ=北京, ATJ=天津, AHE=河北, ASX=山西, ANM=内蒙古, ALN=辽宁...） |
| name | 省名 |
| url | 预报页面路径 |

### 2. 城市列表（按省）

```
GET https://www.nmc.cn/rest/province/{省code}
```

例：`/rest/province/ABJ` → 北京各区/城市：

```json
[{"code": "Wqsps", "province": "北京市", "city": "北京", "url": "/publish/forecast/ABJ/beijing.html"}, ...]
```

| 字段 | 说明 |
|:---|:---|
| code | 城市短码（Wqsps=北京，非气象站编号！） |
| city | 城市名 |
| province | 所在省 |
| url | 城市预报页路径 |

### 3. 天气（实况+预报+空气质量+预警）⭐核心接口

```
GET https://www.nmc.cn/rest/weather?stationid={城市code}
```

例：`/rest/weather?stationid=Wqsps`（北京）

```json
{
  "msg": "success",
  "code": 0,
  "data": {
    "real": { ... },      // 实时实况
    "predict": { ... },   // 多日预报
    "air": { ... },       // 空气质量
    "tempchart": ...,     // 温度趋势图数据
    "passedchart": ...,   // 历史气温
    "climate": ...,       // 气候背景
    "radar": ...          // 雷达
  }
}
```

#### real（实况）

```json
{
  "station": {"code": "Wqsps", "province": "北京市", "city": "北京", "url": "..."},
  "publish_time": "2026-08-03 19:10",
  "weather": {
    "temperature": 26.4, "temperatureDiff": -2.0,
    "airpressure": 9999.0, "humidity": 87.0, "rain": 2.1,
    "rcomfort": 74, "icomfort": 1,
    "info": "中雨", "img": "8", "feelst": 30.9
  },
  "wind": {"direct": "东北风", "degree": 19.0, "power": "微风", "speed": 0.9},
  "warn": {"alert": "2026年08月03日06时北京市气象台发布暴雨蓝色预警信号", "pic": "https://image.nmc.cn/assets/..."},
  "sunriseSunset": {...}
}
```

| 字段 | 说明 |
|:---|:---|
| weather.temperature | 气温 ℃ |
| weather.feelst | 体感温度 ℃ |
| weather.humidity | 相对湿度 % |
| weather.rain | 降水量 mm |
| weather.info | 天气现象（中雨/多云...） |
| weather.img | 天气图标编号 |
| wind.direct/power/speed | 风向/风力/风速 |
| warn.alert | 预警文本（无预警时为空） |
| publish_time | 实况发布时间 |

**缺测值用 9999 占位**（如 airpressure=9999.0、info=9999）。

#### predict（预报）

```json
{
  "station": {...},
  "publish_time": "2026-08-03 20:00",
  "detail": [
    {
      "date": "2026-08-03",
      "pt": "2026-08-03 20:00",
      "day": {"weather": {"info": "9999", "img": "9999", "temperature": "9999"},
              "wind": {"direct": "9999", "power": "9999"}},
      "night": {"weather": {"info": "雷阵雨", "img": "4", "temperature": "24"},
                "wind": {"direct": "东风", "power": "微风"}},
      "precipitation": 23.6
    },
    { "date": "2026-08-04", "day": {"weather": {"info": "雷阵雨", "temperature": "32"}, ...}, ...}
  ]
}
```

- `detail` 数组按日期排列，每天含 `day`（白天）和 `night`（夜间）两个时段
- `precipitation` 为当日预计降水量 mm
- 温度/天气字段为字符串，缺测为 "9999"

#### air（空气质量）

```json
{
  "forecasttime": "2026-08-03 18:00",
  "aqi": 26, "aq": 1, "text": "优",
  "aqiCode": "99006;99008;99009;..."
}
```

| 字段 | 说明 |
|:---|:---|
| aqi | AQI 指数 |
| text | 等级（优/良/轻度污染...） |
| forecasttime | 更新时间 |

## 数据更新频率（精度）

| 数据类型 | 更新频率 | 实测证据 |
|:---|:---|:---|
| 实况 real | 网格产品每 10 分钟滚动更新；对外发布约每小时 | publish_time=19:10 |
| 预报 predict | 每天多次（约 08/11/14/17/20 时发布） | publish_time=20:00 |
| 空气质量 air | 约每小时 | forecasttime=18:00 |
| 预警 warn | 随实况更新，气象台发布后即出现 | — |

> 官方口径：融合 6 万自动站 + 1km 网格产品，网格逐 10 分钟滚动更新，自动站分钟级滚动更新，实况逐小时订正。

## 使用注意

1. **stationid 用城市短码**（Wqsps），不是气象站 5 位编号（54511 返回空 data）
2. **城市 code 固定不变**，脚本已做本地缓存（`city_cache.json`），查询过的城市下次直接读缓存
3. 请求需带浏览器 User-Agent，否则可能被拦
4. 接口为公开免费，无官方文档/无速率限制声明，请勿高频调用
