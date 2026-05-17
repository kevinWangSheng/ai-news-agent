# 015 · Design — Consumption UX 细节

## 1. Source tier 映射(`frontend/lib/tier.ts`)

```typescript
export type SourceTier = "official" | "expert" | "github" | "twitter" | "aggregator" | "chinese" | "manual";

export const TIER_META: Record<SourceTier, {emoji: string; label: string; color: string; bgClass: string}> = {
  official:   { emoji: "🏛️", label: "官方",  color: "#7c3aed", bgClass: "bg-violet-100 dark:bg-violet-900/30 text-violet-700 dark:text-violet-300" },
  expert:     { emoji: "✍️", label: "专家",  color: "#0891b2", bgClass: "bg-cyan-100 dark:bg-cyan-900/30 text-cyan-700 dark:text-cyan-300" },
  github:     { emoji: "💻", label: "GitHub",color: "#374151", bgClass: "bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300" },
  twitter:    { emoji: "🐦", label: "Tweet", color: "#1d9bf0", bgClass: "bg-sky-100 dark:bg-sky-900/30 text-sky-700 dark:text-sky-300" },
  aggregator: { emoji: "📰", label: "聚合",  color: "#ea580c", bgClass: "bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300" },
  chinese:    { emoji: "🇨🇳", label: "中文",  color: "#dc2626", bgClass: "bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300" },
  manual:     { emoji: "✋", label: "手动",  color: "#6b7280", bgClass: "bg-stone-100 dark:bg-stone-800 text-stone-700 dark:text-stone-300" },
};

const OFFICIAL_BLOGS = new Set([
  "OpenAI Blog","Anthropic News","Claude Blog","Google AI Blog","Google DeepMind",
  "Meta AI Blog","xAI News","Mistral News","Qwen Blog","Cohere Blog",
  "HuggingFace Blog","LangChain Blog","LlamaIndex Blog","AutoGen / AG2",
  "Thinking Machines Lab","Cognition (Devin)","Cursor","Reka","Liquid AI",
  "Sierra","Glean","Magic.dev","Browserbase","World Labs","AMI Labs (LeCun)",
  "Manus","Genspark",
]);

const EXPERT_BLOGS = new Set([
  "Simon Willison's Weblog","Sebastian Raschka","Andrej Karpathy","Lilian Weng",
  "Eugene Yan","Chip Huyen","Hamel Husain","Philipp Schmid","Latent Space (swyx)",
]);

const AGGREGATORS = new Set([
  "The Batch (DeepLearning.AI)","Import AI (Jack Clark)","AINews (smol.ai)",
  "Latent Space Newsletter","arXiv AI","arXiv Multi-Agent Systems",
]);

export function getSourceTier(item: {source_type: string; source_name: string | null}): SourceTier {
  if (item.source_type === "github") return "github";
  if (item.source_type === "twitter") return "twitter";
  if (item.source_type === "chinese") return "chinese";
  if (item.source_type === "manual") return "manual";
  const n = item.source_name || "";
  if (OFFICIAL_BLOGS.has(n)) return "official";
  if (EXPERT_BLOGS.has(n)) return "expert";
  if (AGGREGATORS.has(n)) return "aggregator";
  return "expert"; // 默认归专家(rss 类型基本都是)
}

// Tier → 后端 source_name 列表反向映射,给后端 filter 用
export const TIER_TO_SOURCE_NAMES: Record<SourceTier, string[] | "BY_TYPE"> = {
  official: [...OFFICIAL_BLOGS],
  expert:   [...EXPERT_BLOGS],
  aggregator:[...AGGREGATORS],
  github:    "BY_TYPE",   // 后端按 source_type='github' 过滤
  twitter:   "BY_TYPE",
  chinese:   "BY_TYPE",
  manual:    "BY_TYPE",
};
```

后端实现:`tier` 参数到达后,前端可以传 `tier=official` 或 `tier=github`;后端根据这个映射(也保留 set 一份在 backend/app/api/utils/tier.py)做 SQL filter。

## 2. ItemCard 变体系统

```typescript
type Variant = "top" | "hot" | "normal" | "dim";

function autoVariant(item: Item, viewed: boolean): Variant {
  if (viewed) return "dim";
  if (item.final_score === null) return "normal";
  if (item.final_score >= 10) return "top";
  if (item.final_score >= 9) return "hot";
  if (item.final_score < 7) return "dim";
  return "normal";
}

const VARIANT_STYLES = {
  top:    "border-2 border-amber-400 dark:border-amber-500 p-5 shadow-md",
  hot:    "border border-orange-300 dark:border-orange-700 p-4 shadow-sm",
  normal: "border border-neutral-200 dark:border-neutral-800 p-4",
  dim:    "border border-neutral-200/50 dark:border-neutral-800/50 p-3 opacity-70",
};

const VARIANT_TITLE = {
  top:    "text-lg font-semibold",
  hot:    "text-base font-medium",
  normal: "font-medium",
  dim:    "text-sm",
};

// emoji 标签(可叠加)
function getCardEmojis(item: Item, viewed: boolean): string[] {
  const emojis = [];
  if (item.final_score === 10) emojis.push("⭐");
  else if ((item.final_score ?? 0) >= 9) emojis.push("🔥");
  const hours = (Date.now() - new Date(item.ingested_at).getTime()) / 3.6e6;
  if (hours <= 24) emojis.push("🆕");
  // 16+ 后:多源讨论加 📡 (后端给 cluster_size > 1)
  return emojis;
}
```

## 3. URL state schema(`/inbox`)

```
?since=24h|7d|all              默认 all
&tier=official|expert|github|...  可空
&topic=mcp                      slug,可空
&min_score=6|8                  默认 6
&status=inbox|kept|archived|all   默认 inbox
&sort=score|time                 默认 score
&q=...                          可空
```

`useFilters()` hook:`const filters = useFilters()` 返回 typed 对象。

后端 list_items 接受相同参数(单独 tier → 反查 source_name 列表)。

## 4. Score breakdown 显示

DB 里 `score_breakdown` 形如:
```json
{
  "base": 7.5,
  "final": 9.0,
  "tag_boost": 1.5,
  "cold_start": true,
  "focus_hits": ["mcp", "agent"],
  "time_decay": 0.0,
  "entity_boost": 0.0,
  "source_boost": 0.0
}
```

**Chip(卡片底部 hover):**
`9.0 = 7.5 base + 1.5 #mcp + 0.5 Anthropic`

**Panel(详情页常驻):**
```
评分 9.0 = 基础 7.5 + 主题加权 1.5 + 信源加权 0.0
匹配关键词:#mcp #agent
信源:Anthropic News(无 boost)
时间衰减:0.0(新进)
⚠ 冷启动中:还没到 50 次交互,推荐未启用
```

## 5. 键盘流(`react-hotkeys-hook`)

```typescript
useHotkeys("j", () => focusedIdx.next());
useHotkeys("k", () => focusedIdx.prev());
useHotkeys("o,enter", () => router.push(`/item/${focusedId}`));
useHotkeys("s", () => keep(focusedId));
useHotkeys("e", () => archive(focusedId));
useHotkeys("x", () => trash(focusedId));
useHotkeys("/", (e) => { e.preventDefault(); searchRef.current?.focus(); });
useHotkeys("shift+/", () => setShowCheatsheet(true));   // ? 键
useHotkeys("g+i", () => router.push("/inbox"));
useHotkeys("g+l", () => router.push("/library"));
useHotkeys("g+t", () => router.push("/topics"));
useHotkeys("meta+z", () => undoLast());
```

Cheatsheet modal 用 cmdk 或自实现。

## 6. 撤销实现细节

```typescript
type PendingAction = { itemId: number; from: string; to: string; timer: NodeJS.Timeout };
const [pending, setPending] = useState<PendingAction | null>(null);

function archive(itemId: number) {
  // 1. 乐观:从 UI 列表移除(用 swr mutate)
  mutate(`/api/items?${filters}`, (data) => data.items.filter(i => i.id !== itemId));
  
  // 2. 启动 5s timer
  const timer = setTimeout(() => {
    patchItem(itemId, { status: "archived" });
    setPending(null);
  }, 5000);
  setPending({ itemId, from: "inbox", to: "archived", timer });
  
  // 3. toast
  toast(`已归档 #${itemId}`, {
    duration: 5000,
    action: { label: "撤销", onClick: () => undo() },
  });
}

function undo() {
  if (!pending) return;
  clearTimeout(pending.timer);
  mutate(`/api/items?${filters}`); // refetch 还原
  setPending(null);
}
```

## 7. 后端改动(api/routes/items.py)

```python
@router.get("/api/items")
async def list_items(
    status: str = "inbox",
    source_name: str | None = None,
    topic: str | None = None,
    since: str | None = None,        # "24h" / "7d"
    min_score: float | None = None,
    tier: str | None = None,
    limit: int = 50,
    cursor: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(Item).where(Item.status == status)
    if source_name: q = q.where(Item.source_name == source_name)
    if min_score is not None: q = q.where(Item.final_score >= min_score)
    if since:
        delta = parse_since(since)  # "24h"->1天 / "7d"->7天
        q = q.where(Item.ingested_at >= datetime.now(timezone.utc) - delta)
    if tier:
        from app.api.utils.tier import resolve_tier
        type_or_names = resolve_tier(tier)
        if isinstance(type_or_names, list):
            q = q.where(Item.source_name.in_(type_or_names))
        else:
            q = q.where(Item.source_type == type_or_names)
    # ... 现有 topic / cursor 逻辑
    # join interactions 拿 viewed_at(LEFT OUTER JOIN + MAX(ts) WHERE action='view')
    # 返回 ItemListOut(items=..., next_cursor=...)
```

`POST /api/items/bulk`:

```python
class BulkRequest(BaseModel):
    ids: list[int]
    action: Literal["kept", "archived", "trashed"]

@router.post("/api/items/bulk")
async def bulk_patch(body: BulkRequest, db: AsyncSession = Depends(get_db)):
    await db.execute(update(Item).where(Item.id.in_(body.ids)).values(status=body.action))
    await db.commit()
    return {"updated": len(body.ids)}
```

## 8. 已读判定的实现

后端 `list_items` 加 left join:

```python
viewed_subq = (
    select(Interaction.item_id, func.max(Interaction.created_at).label("viewed_at"))
    .where(Interaction.action == "view")
    .group_by(Interaction.item_id)
    .subquery()
)
q = (
    select(Item, viewed_subq.c.viewed_at)
    .outerjoin(viewed_subq, viewed_subq.c.item_id == Item.id)
    .where(Item.status == status)
)
```

ItemOut Pydantic 加 `viewed_at: datetime | None`,前端按此渲染 variant=dim。

## 9. 不使用的方案 + 理由

- ❌ shadcn/ui 组件:008-frontend-scaffold 时决议跳过,继续 Tailwind 手写,避免引入交互式 CLI
- ❌ React Context 状态管理:URL + SWR 就够,Context 会让 SSR 复杂
- ❌ tier 字段进 DB:UI 概念,不污染数据层。映射在前端 + 后端 utils 各一份(同步靠 lint)
- ❌ Sonner 替换为自实现 toast:Sonner 体积小、稳定,直接用
- ❌ 大改 sidebar:本 change 不动 sidebar 结构,只动 TopBar + Inbox 主区

## 10. 风险与降级

- **react-window 在 SSR 模式可能有 hydration mismatch** → 用 `'use client'` + 客户端 only 渲染列表,接受首屏稍晚
- **markdown 渲染 GitHub README 可能有奇怪 HTML 注入** → rehype-raw 慎用,只放 sanitize 后的(优先纯 GFM)
- **键盘流跟 input focus 冲突** → 监听只在 `document.activeElement.tagName !== 'INPUT' && 'TEXTAREA'` 时触发
- **600+ 条乐观 mutate 性能** → 用 SWR `mutate(key, fn, { revalidate: false })` 局部更新,不全量重拉
