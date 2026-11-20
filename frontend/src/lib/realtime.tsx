import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from "react";

type Handler = (data: any) => void; // eslint-disable-line @typescript-eslint/no-explicit-any

interface RealtimeCtx {
  connected: boolean;
  subscribe: (event: string, handler: Handler) => () => void;
}

const Ctx = createContext<RealtimeCtx>({ connected: false, subscribe: () => () => {} });

/** Conexão WebSocket única para o app, com reconexão exponencial e pub/sub por evento. */
export function RealtimeProvider({ children }: { children: ReactNode }) {
  const [connected, setConnected] = useState(false);
  const handlers = useRef(new Map<string, Set<Handler>>());

  useEffect(() => {
    let ws: WebSocket | null = null;
    let retry = 0;
    let timer: number | undefined;
    let ping: number | undefined;
    let closed = false;

    const connect = () => {
      const proto = location.protocol === "https:" ? "wss" : "ws";
      ws = new WebSocket(`${proto}://${location.host}/ws`);
      ws.onopen = () => {
        retry = 0;
        setConnected(true);
        ping = window.setInterval(() => ws?.readyState === WebSocket.OPEN && ws.send("ping"), 25_000);
      };
      ws.onmessage = (e) => {
        const { event, data } = JSON.parse(e.data);
        handlers.current.get(event)?.forEach((h) => h(data));
        handlers.current.get("*")?.forEach((h) => h({ event, data }));
      };
      ws.onclose = () => {
        setConnected(false);
        window.clearInterval(ping);
        if (!closed) timer = window.setTimeout(connect, Math.min(10_000, 500 * 2 ** retry++));
      };
    };
    connect();
    return () => {
      closed = true;
      window.clearTimeout(timer);
      window.clearInterval(ping);
      ws?.close();
    };
  }, []);

  const subscribe = useCallback((event: string, handler: Handler) => {
    if (!handlers.current.has(event)) handlers.current.set(event, new Set());
    handlers.current.get(event)!.add(handler);
    return () => {
      handlers.current.get(event)?.delete(handler);
    };
  }, []);

  return <Ctx.Provider value={{ connected, subscribe }}>{children}</Ctx.Provider>;
}

export const useRealtime = () => useContext(Ctx);

/** Assina um evento enquanto o componente estiver montado (handler sempre atualizado). */
export function useEvent(event: string, handler: Handler) {
  const { subscribe } = useRealtime();
  const ref = useRef(handler);
  ref.current = handler;
  useEffect(() => subscribe(event, (d) => ref.current(d)), [event, subscribe]);
}
