# GiftRadar 前端面板

React + Vite + TypeScript + Tailwind v4 + Recharts + @tanstack/react-query 构建的数据看板。

完整使用说明见仓库根目录的 [`README.md`](../README.md) 与 [`docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md)。

```bash
npm install
npm run dev
```

开发模式下 `/api` 请求会被 `vite.config.ts` 中的代理转发到本地 `http://localhost:8000` 的后端服务。
