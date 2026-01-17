export type State = "ASK_MEMBER" | "ASK_ORDER" | "COMPLETED";

export type ApiOk<T> = { ok: true } & T;
export type ApiNg = {
  ok: false;
  state?: State; // ← state は必須にしない（HTML 400 対策）
  error: {
    code: string;
    message: string;
  };
  prompt?: string;
};



async function req<T>(path: string, init: RequestInit = {}): Promise<ApiOk<T> | ApiNg> {
  const headers = new Headers(init.headers);

  // ここが重要：常にJSONとして送る
  if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const res = await fetch(path, {
    ...init,
    headers,
    // これも重要：cookieが必要なら送る（不要でも害は少ない）
    credentials: "same-origin",
  });

  // 400/500時に原因が見えるようにしておく（デバッグ用）
  const text = await res.text();
  try {
    return JSON.parse(text);
  } catch {
    // JSONじゃない（HTMLエラー）なら、そのまま返して原因を見える化
    return { ok: false, state: "ASK_MEMBER", error: { code: "HTTP_ERROR", message: text } } as ApiNg;
  }
}

export const api = {
  createSession: () =>
    req<{ session_id: string; state: State; prompt: string }>("/api/sessions", {
      method: "POST",
      body: JSON.stringify({}),
    }),

  memberLookup: (sid: string, member_number: string) =>
    req<{ state: State; member: { member_number: string; name: string }; prompt: string }>(
      `/api/sessions/${sid}/member-lookup`,
      { method: "POST", body: JSON.stringify({ member_number }) }
    ),

  order: (sid: string, order_number: string, quantity: number) =>
    req<{ state: State; order: { order_number: string; quantity: number }; thank_you_message: string }>(
      `/api/sessions/${sid}/order`,
      { method: "POST", body: JSON.stringify({ order_number, quantity }) }
    ),
};
