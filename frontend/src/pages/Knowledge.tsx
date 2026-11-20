import clsx from "clsx";
import { BookOpen, FlaskConical, Pencil, Plus, Search, Trash2, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { PageHeader, Spinner, Tag, Toggle } from "../components/ui";
import { api } from "../lib/api";
import { num, since } from "../lib/format";
import type { Article, Source } from "../lib/types";

const EMPTY: Partial<Article> = { title: "", category: "", content: "", tags: [], active: true };

function Editor({ article, onClose, onSaved }: { article: Partial<Article>; onClose: () => void; onSaved: () => void }) {
  const [form, setForm] = useState(article);
  const [tags, setTags] = useState((article.tags ?? []).join(", "));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const save = async () => {
    setSaving(true);
    setError(null);
    const body = { ...form, tags: tags.split(",").map((t) => t.trim()).filter(Boolean) };
    try {
      if (form.id) await api.updateArticle(form.id, body);
      else await api.createArticle(body);
      onSaved();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao salvar");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-900/30 backdrop-blur-[1px]" onClick={onClose}>
      <div className="animate-pop flex h-full w-full max-w-xl flex-col bg-white shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">
          <h2 className="font-semibold">{form.id ? "Editar artigo" : "Novo artigo"}</h2>
          <button onClick={onClose} className="btn-ghost p-1.5" aria-label="Fechar">
            <X size={18} />
          </button>
        </div>
        <div className="flex-1 space-y-4 overflow-y-auto p-6">
          <label className="block">
            <span className="mb-1 block text-sm font-medium">Título</span>
            <input className="input" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
          </label>
          <div className="grid grid-cols-2 gap-4">
            <label className="block">
              <span className="mb-1 block text-sm font-medium">Categoria</span>
              <input className="input" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} />
            </label>
            <label className="block">
              <span className="mb-1 block text-sm font-medium">Tags (separadas por vírgula)</span>
              <input className="input" value={tags} onChange={(e) => setTags(e.target.value)} />
            </label>
          </div>
          <label className="block">
            <span className="mb-1 block text-sm font-medium">Conteúdo</span>
            <span className="mb-2 block text-xs text-slate-500">
              Escreva como se estivesse falando com o cliente. Cada parágrafo vira um trecho indexado para a IA.
            </span>
            <textarea
              className="input min-h-[300px] leading-relaxed"
              value={form.content}
              onChange={(e) => setForm({ ...form, content: e.target.value })}
            />
          </label>
          <div className="flex items-center justify-between rounded-lg bg-slate-50 px-4 py-3">
            <div>
              <p className="text-sm font-medium">Ativo</p>
              <p className="text-xs text-slate-500">Artigos inativos não são usados pela IA.</p>
            </div>
            <Toggle checked={!!form.active} onChange={(v) => setForm({ ...form, active: v })} label="Ativo" />
          </div>
          {error && <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
        </div>
        <div className="flex justify-end gap-2 border-t border-slate-200 px-6 py-4">
          <button className="btn-secondary" onClick={onClose}>
            Cancelar
          </button>
          <button className="btn-primary" onClick={save} disabled={saving}>
            {saving && <Spinner className="h-3.5 w-3.5" />} Salvar e reindexar
          </button>
        </div>
      </div>
    </div>
  );
}

function Playground() {
  const [query, setQuery] = useState("posso parcelar no cartão?");
  const [result, setResult] = useState<{ took_ms: number; chunks_indexed: number; results: Source[] } | null>(null);
  const [loading, setLoading] = useState(false);

  const run = async () => {
    if (query.trim().length < 2) return;
    setLoading(true);
    setResult(await api.searchKnowledge(query).finally(() => setLoading(false)));
  };

  useEffect(() => {
    run();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <section className="card p-5">
      <div className="flex items-center gap-2">
        <span className="rounded-lg bg-brand-100 p-1.5 text-brand-700">
          <FlaskConical size={15} />
        </span>
        <div>
          <h2 className="text-sm font-semibold">Playground de busca (RAG)</h2>
          <p className="text-xs text-slate-500">Teste o que a IA encontra para uma pergunta de cliente.</p>
        </div>
      </div>
      <form
        className="mt-4 flex gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          run();
        }}
      >
        <input className="input" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Pergunta do cliente…" />
        <button className="btn-primary" disabled={loading}>
          {loading ? <Spinner className="h-3.5 w-3.5" /> : <Search size={15} />}
        </button>
      </form>
      {result && (
        <div className="mt-4">
          <p className="mb-2 text-[11.5px] text-slate-500">
            {result.results.length} trechos relevantes · {num(result.chunks_indexed)} indexados · {num(result.took_ms, 2)} ms
          </p>
          <ul className="space-y-2">
            {result.results.map((r, i) => (
              <li key={i} className="rounded-xl border border-slate-200 p-3">
                <div className="mb-1.5 flex items-center gap-2">
                  <span className="text-[13px] font-medium">{r.title}</span>
                  <span
                    className={clsx(
                      "ml-auto rounded px-1.5 py-0.5 font-mono text-[11px] font-medium",
                      r.score >= 0.38 ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-500",
                    )}
                    title="Pontuação de relevância — a IA usa trechos acima de 38%"
                  >
                    {Math.round(r.score * 100)}%
                  </span>
                </div>
                <p className="line-clamp-3 text-[12.5px] leading-relaxed text-slate-600">{r.text}</p>
              </li>
            ))}
            {result.results.length === 0 && <li className="text-sm text-slate-400">Nada encontrado — a IA ofereceria um especialista.</li>}
          </ul>
        </div>
      )}
    </section>
  );
}

export default function Knowledge() {
  const [articles, setArticles] = useState<Article[] | null>(null);
  const [editing, setEditing] = useState<Partial<Article> | null>(null);
  const [filter, setFilter] = useState("");
  const [category, setCategory] = useState("");

  const load = () => api.articles().then(setArticles);
  useEffect(() => {
    load();
  }, []);

  const categories = useMemo(() => [...new Set(articles?.map((a) => a.category))].sort(), [articles]);
  const visible = (articles ?? []).filter(
    (a) =>
      (!category || a.category === category) &&
      (a.title + a.content).toLowerCase().includes(filter.toLowerCase()),
  );

  return (
    <div className="scroll-thin h-full overflow-y-auto p-8">
      <PageHeader
        title="Base de conhecimento"
        subtitle="Fonte oficial das respostas da IA. Alterações são reindexadas na hora."
        actions={
          <button className="btn-primary" onClick={() => setEditing(EMPTY)}>
            <Plus size={15} /> Novo artigo
          </button>
        }
      />
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1fr_400px]">
        <div>
          <div className="mb-4 flex flex-wrap gap-2">
            <div className="relative w-64">
              <Search size={15} className="absolute top-1/2 left-3 -translate-y-1/2 text-slate-400" />
              <input className="input pl-9" placeholder="Filtrar artigos…" value={filter} onChange={(e) => setFilter(e.target.value)} />
            </div>
            <button
              onClick={() => setCategory("")}
              className={clsx("pill", !category ? "bg-slate-900 text-white ring-slate-900" : "bg-white text-slate-600 ring-slate-200")}
            >
              Todas
            </button>
            {categories.map((c) => (
              <button
                key={c}
                onClick={() => setCategory(c === category ? "" : c)}
                className={clsx("pill", category === c ? "bg-slate-900 text-white ring-slate-900" : "bg-white text-slate-600 ring-slate-200")}
              >
                {c}
              </button>
            ))}
          </div>
          {!articles ? (
            <Spinner />
          ) : (
            <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
              {visible.map((a) => (
                <article key={a.id} className={clsx("card group flex flex-col p-4", !a.active && "opacity-60")}>
                  <div className="flex items-start gap-3">
                    <span className="rounded-lg bg-slate-100 p-2 text-slate-500">
                      <BookOpen size={15} />
                    </span>
                    <div className="min-w-0 flex-1">
                      <h3 className="text-sm font-semibold">{a.title}</h3>
                      <p className="text-xs text-slate-500">
                        {a.category} · atualizado {since(a.updated_at)}
                      </p>
                    </div>
                    <div className="flex opacity-0 transition group-hover:opacity-100">
                      <button className="btn-ghost p-1.5" onClick={() => setEditing(a)} aria-label="Editar">
                        <Pencil size={14} />
                      </button>
                      <button
                        className="btn-ghost p-1.5 hover:text-red-600"
                        aria-label="Excluir"
                        onClick={async () => {
                          if (confirm(`Excluir "${a.title}"?`)) {
                            await api.deleteArticle(a.id);
                            load();
                          }
                        }}
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                  <p className="mt-3 line-clamp-3 flex-1 text-[13px] leading-relaxed text-slate-600">{a.content}</p>
                  <div className="mt-3 flex items-center gap-1.5">
                    {a.tags.slice(0, 3).map((t) => (
                      <Tag key={t}>{t}</Tag>
                    ))}
                    <span className="ml-auto text-[11.5px] text-slate-400">usado {num(a.hits)}×</span>
                  </div>
                </article>
              ))}
            </div>
          )}
        </div>
        <div className="xl:sticky xl:top-0 xl:self-start">
          <Playground />
        </div>
      </div>
      {editing && (
        <Editor
          article={editing}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null);
            load();
          }}
        />
      )}
    </div>
  );
}
