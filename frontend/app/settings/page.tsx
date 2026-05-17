"use client";
import { API_BASE } from "@/lib/api/client";

const BOOKMARKLET_JS = `javascript:(function(){var api=window.HUB_API||'${"http://localhost:8000"}';var sel=window.getSelection().toString();fetch(api+'/api/ingest',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url:location.href,title:document.title,content:sel||null,source_type:'manual',source_name:'bookmarklet'})}).then(function(r){return r.json();}).then(function(j){alert('已投喂 #'+j.item_id+(j.created?'':' (已存在)'))}).catch(function(e){alert('投喂失败: '+e);});})();`;

export default function SettingsPage() {
  return (
    <section className="max-w-2xl space-y-8">
      <div>
        <h1 className="text-2xl font-semibold">设置</h1>
        <p className="text-sm text-neutral-500 mt-1">当前 API: <code className="bg-neutral-100 dark:bg-neutral-800 px-1.5 py-0.5 rounded">{API_BASE}</code></p>
      </div>

      <section>
        <h2 className="text-lg font-medium mb-2">Bookmarklet 安装</h2>
        <p className="text-sm text-neutral-500 mb-3">把下面这个按钮拖到浏览器书签栏。之后在任何网页点击它,当前页会被投喂到 hub。</p>
        <p>
          <a className="inline-block px-4 py-2 bg-neutral-900 text-white dark:bg-neutral-100 dark:text-neutral-900 rounded font-medium" href={BOOKMARKLET_JS}>
            📥 投喂到 hub
          </a>
        </p>
        <details className="mt-4">
          <summary className="text-sm cursor-pointer text-neutral-500">显示原始 javascript:...</summary>
          <pre className="mt-2 p-3 text-xs bg-neutral-100 dark:bg-neutral-800 rounded overflow-x-auto">{BOOKMARKLET_JS}</pre>
        </details>
        <p className="text-xs text-neutral-500 mt-3">
          注:bookmarklet 在 https 页面调本机 http://localhost 可能被 mixed-content 拦截,后端 CORS 已配 <code>allow_origins=["*"]</code>。
          详情见 <code>docs/install-bookmarklet.md</code>。
        </p>
      </section>

      <section>
        <h2 className="text-lg font-medium mb-2">键盘快捷键</h2>
        <ul className="text-sm space-y-1 text-neutral-600 dark:text-neutral-400">
          <li><kbd className="px-1.5 py-0.5 bg-neutral-100 dark:bg-neutral-800 rounded">/</kbd> 聚焦顶部搜索框</li>
          <li><kbd className="px-1.5 py-0.5 bg-neutral-100 dark:bg-neutral-800 rounded">⌘K</kbd> / <kbd className="px-1.5 py-0.5 bg-neutral-100 dark:bg-neutral-800 rounded">Ctrl+K</kbd> 唤起命令面板</li>
          <li><kbd className="px-1.5 py-0.5 bg-neutral-100 dark:bg-neutral-800 rounded">g</kbd> 然后 <kbd className="px-1.5 py-0.5 bg-neutral-100 dark:bg-neutral-800 rounded">i</kbd> / <kbd className="px-1.5 py-0.5 bg-neutral-100 dark:bg-neutral-800 rounded">l</kbd> / <kbd className="px-1.5 py-0.5 bg-neutral-100 dark:bg-neutral-800 rounded">t</kbd> / <kbd className="px-1.5 py-0.5 bg-neutral-100 dark:bg-neutral-800 rounded">e</kbd> / <kbd className="px-1.5 py-0.5 bg-neutral-100 dark:bg-neutral-800 rounded">d</kbd> 去 inbox/library/topics/entities/digest</li>
        </ul>
      </section>
    </section>
  );
}
