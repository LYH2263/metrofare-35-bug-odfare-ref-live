# 13-metrofare（地铁票价）

Metrofare — 站间最短站数 + 分段票价表

## 启动

```bash
docker compose up --build
```

| 入口 | 地址 |
| --- | --- |
| 前端 | http://localhost:4200 |
| API | http://localhost:9200 |

## 主链

选起终点站 → 按站数/里程规则算票价 → 出示票价卡

## 点对点一口价

- `POST /api/flat-fares` 为有向起终点对登记一口价（同对重复登记返回 409）
- 询价 `POST /api/quote` 命中一口价时应付按一口价，回包 `fare_source=flat`，
  同时给出 `hops`/`path`（最短途经站）和分段表 `reference_fare`；未命中回退分段表
- `DELETE /api/flat-fares/{start}/{end}` 后该 OD 回到分段表，历史记录快照不改写
- `persist=false` 只读试算不落库

## 技术栈

Python 3.12 + FastAPI + SQLite；Vue 3 + Vite + Nginx。
