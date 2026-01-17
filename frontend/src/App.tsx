import { useEffect, useState } from "react";
import { api } from "./api";


type View =
  | { state: "ASK_MEMBER"; prompt: string; error?: string }
  | { state: "ASK_ORDER"; prompt: string; error?: string }
  | { state: "COMPLETED"; thankYou: string };


const SID_KEY = "demo_session_id";

export default function App() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [view, setView] = useState<View>({ state: "ASK_MEMBER", prompt: "初期化中..." });

  const startNew = async () => {
    localStorage.removeItem(SID_KEY);
    const r = await api.createSession();
    if (r.ok) {
      setSessionId(r.session_id);
      localStorage.setItem(SID_KEY, r.session_id);
      setView({ state: "ASK_MEMBER", prompt: r.prompt });

    }
  };

  useEffect(() => {
    const sid = localStorage.getItem(SID_KEY);
    if (sid) {
      setSessionId(sid);
      setView({ state: "ASK_MEMBER", prompt: "組合員番号を入力してください" });
      return;
    }
    startNew();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const onMemberSubmit = async (member_number: string) => {
    console.log("member_number=", JSON.stringify(member_number));
    if (!sessionId) return;
    const r = await api.memberLookup(sessionId, member_number);
    if (r.ok) {
      setView({ state: "ASK_ORDER", prompt: r.prompt });
    } else {
      setView({ state: "ASK_MEMBER", prompt: r.prompt ?? "組合員番号を入力してください", error: r.error.message });
    }
  };

  const onOrderSubmit = async (order_number: string, quantity: number) => {
    if (!sessionId) return;
    const r = await api.order(sessionId, order_number, quantity);
    if (r.ok) {
      setView({ state: "COMPLETED", thankYou: r.thank_you_message });
    } else {
      if (r.error.code === "ALREADY_COMPLETED") {
        setView({ state: "COMPLETED", thankYou: r.error.message });
      } else {
        setView({ state: "ASK_ORDER", prompt: r.prompt ?? "注文番号を入力してください", error: r.error.message });
      }
    }
  };

  return (
    <div style={{ maxWidth: 520, margin: "40px auto", fontFamily: "sans-serif" }}>
      <h2>電話自動応対 擬似UI</h2>
      <p style={{ color: "#666" }}>session: {sessionId ?? "-"}</p>

      {view.state === "ASK_MEMBER" && (
        <MemberStep prompt={view.prompt} error={view.error} onSubmit={onMemberSubmit} />
      )}
      {view.state === "ASK_ORDER" && (
        <OrderStep prompt={view.prompt} error={view.error} onSubmit={onOrderSubmit} />
      )}
      {view.state === "COMPLETED" && <CompleteStep thankYou={view.thankYou} onRestart={startNew} />}
    </div>
  );
}

function ErrorText({ msg }: { msg?: string }) {
  if (!msg) return null;
  return <div style={{ color: "crimson", marginTop: 8 }}>{msg}</div>;
}

function MemberStep({
  prompt,
  error,
  onSubmit,
}: {
  prompt: string;
  error?: string;
  onSubmit: (n: string) => void;
}) {
  const [val, setVal] = useState("");
  return (
    <div>
      <h3>{prompt}</h3>
      <input value={val} onChange={(e) => setVal(e.target.value)} placeholder="12345678" />
      <button style={{ marginLeft: 8 }} onClick={() => onSubmit(val.trim())}>
        送信
      </button>
      <ErrorText msg={error} />
    </div>
  );
}

function OrderStep({
  prompt,
  error,
  onSubmit,
}: {
  prompt: string;
  error?: string;
  onSubmit: (o: string, q: number) => void;
}) {
  const [order, setOrder] = useState("");
  const [qty, setQty] = useState(1);

  return (
    <div>
      <h3>{prompt}</h3>
      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
        <input value={order} onChange={(e) => setOrder(e.target.value)} placeholder="10020030" />
        <input type="number" min={1} value={qty} onChange={(e) => setQty(Number(e.target.value))} style={{ width: 80 }} />
        <button onClick={() => onSubmit(order.trim(), qty)}>送信</button>
      </div>
      <ErrorText msg={error} />
    </div>
  );
}

function CompleteStep({ thankYou, onRestart }: { thankYou: string; onRestart: () => void }) {
  return (
    <div>
      <h3>{thankYou}</h3>
      <button onClick={onRestart}>最初から</button>
    </div>
  );
}
