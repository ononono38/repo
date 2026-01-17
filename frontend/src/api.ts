export type State = "ASK_MEMBER" | "ASK_ORDER" | "COMPLETED";

export type ApiOk<T> = { ok: true } & T;
export type ApiNg = {
  ok: false;
  state: State;
  error: { code: string; message: string };
  prompt?: string;
};

async function req<T>(path: string, init?: RequestInit): Promise<ApiOk<T> | ApiNg> {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  return await res.json();
}

export const api = {
  createSession: () =>
    req<{ session_id: string; state: State; prompt: string }>("/api/sessions", {
      method: "POST",
      body: "{}",
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
