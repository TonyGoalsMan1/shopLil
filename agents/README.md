# LYLILI Autonomous Agents

Агенты сами совершенствуют сайт, сканируя что крутого в интернете.

## Агенты
1. **TrendScoutAgent** (`trend_scout.py`) — каждые 3ч парсит Awwwards/Linear/Stripe/Telegram Blog, вытаскивает ключевые слова (glass, bento, aurora, 3D, gift) и цвета, пишет `memory/trends.json` + рекомендации.
2. **DesignEvolverAgent** (`design_evolver.py`) — читает тренды, делает бэкап `style.css` → `memory/backups/`, выбирает вариант (aurora/midnight/candy) и дописывает эволюционный CSS (hue-rotate, glass boost) прямо в `static/css/style.css`. Не дублирует.
3. **UXOptimizerAgent** (`ux_optimizer.py`) — фиксит доступность (aria-label), lazy-loading, минифицирует в `style.min.css`, добавляет meta description.
4. **ContentCuratorAgent** (`content_curator.py`) — генерирует 2 новые идеи подарков как в Telegram (🦄👑💎🔮) на основе трендов, пишет `memory/content_ideas.json`, автономно добавляет 1 товар в `app.py` PRODUCTS.

## Оркестратор
`agents/orchestrator.py` — запускает всех по очереди, пишет `memory/last_run.json`.

## Запуск
```powershell
pip install -r agents/requirements-agents.txt
python agents/orchestrator.py              # один прогон
python agents/orchestrator.py --loop 60    # вечный loop каждые 60 мин
python agents/orchestrator.py --schedule   # APScheduler: Scout 3h, Evolver 12h, UX 24h
```

## Автономность
- Каждый агент `safe_run()` с логированием в `memory/*.jsonl`
- Состояние в `memory/*.state.json`
- Бэкапы CSS перед мутацией
- Flask трогает `app.py` для hot-reload

## Где смотреть результат
- http://127.0.0.1:5000/ — подарки меняются после эволюции
- `agents/memory/trends.json` — что нашли в интернете
- `agents/memory/backups/` — откат дизайна
