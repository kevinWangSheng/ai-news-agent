"use client";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import rehypeHighlight from "rehype-highlight";
import "highlight.js/styles/github-dark.css";

export function MarkdownRenderer({ source }: { source: string | null | undefined }) {
  if (!source) return null;
  return (
    <div className="markdown-body text-[15px] leading-7 text-neutral-800 dark:text-neutral-100">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw, rehypeHighlight]}
        components={{
          a: ({ href, children }) => <a href={href} target="_blank" rel="noreferrer" className="text-blue-600 underline decoration-blue-300 underline-offset-2 dark:text-blue-400">{children}</a>,
          img: ({ src, alt }) => <img src={src || ""} alt={alt || ""} loading="lazy" className="my-4 max-h-[520px] rounded-xl border border-neutral-200 object-contain dark:border-neutral-800" />,
          h1: ({ children }) => <h1 className="mt-8 mb-3 text-2xl font-semibold tracking-tight">{children}</h1>,
          h2: ({ children }) => <h2 className="mt-7 mb-3 text-xl font-semibold tracking-tight">{children}</h2>,
          h3: ({ children }) => <h3 className="mt-6 mb-2 text-lg font-semibold">{children}</h3>,
          p: ({ children }) => <p className="my-3">{children}</p>,
          ul: ({ children }) => <ul className="my-3 ml-5 list-disc space-y-1">{children}</ul>,
          ol: ({ children }) => <ol className="my-3 ml-5 list-decimal space-y-1">{children}</ol>,
          blockquote: ({ children }) => <blockquote className="my-4 border-l-4 border-neutral-300 pl-4 text-neutral-600 dark:border-neutral-700 dark:text-neutral-300">{children}</blockquote>,
          table: ({ children }) => <div className="my-4 overflow-x-auto rounded-xl border border-neutral-200 dark:border-neutral-800"><table className="min-w-full divide-y divide-neutral-200 text-sm dark:divide-neutral-800">{children}</table></div>,
          th: ({ children }) => <th className="bg-neutral-50 px-3 py-2 text-left font-medium dark:bg-neutral-900">{children}</th>,
          td: ({ children }) => <td className="border-t border-neutral-100 px-3 py-2 align-top dark:border-neutral-800">{children}</td>,
          code: ({ className, children }) => {
            const inline = !className;
            const text = String(children).replace(/\n$/, "");
            if (inline) return <code className="rounded bg-neutral-100 px-1 py-0.5 font-mono text-[0.9em] dark:bg-neutral-800">{children}</code>;
            return (
              <span className="group/code relative block">
                <button type="button" onClick={() => navigator.clipboard?.writeText(text)} className="absolute right-2 top-2 rounded bg-neutral-800/80 px-2 py-1 text-[11px] text-white opacity-0 transition group-hover/code:opacity-100">copy</button>
                <code className={`${className} block overflow-x-auto rounded-xl p-4 font-mono text-sm`}>{children}</code>
              </span>
            );
          },
        }}
      >
        {source}
      </ReactMarkdown>
    </div>
  );
}
