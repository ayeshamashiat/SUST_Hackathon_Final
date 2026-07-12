import { formatBDT, formatRelative } from "@/lib/format";
import { PROVIDER_LABEL, type ProviderId } from "@/lib/agents";
import type { TransactionOut } from "@/lib/types";

function providerLabel(provider: string): string {
  return PROVIDER_LABEL[provider as ProviderId] ?? provider;
}

export function TransactionStream({ transactions }: { transactions: TransactionOut[] }) {
  return (
    <div className="rounded-2xl border border-[#E8EAF0] bg-white overflow-hidden">
      <div className="px-4.5 py-4 border-b border-[#EFF1F6] flex items-center justify-between">
        <span className="font-bold text-[15px]">Recent transactions</span>
      </div>
      <div>
        {transactions.length === 0 && (
          <div className="px-4.5 py-6 text-center text-[13px] text-slate-400">No transactions yet.</div>
        )}
        {transactions.map((t) => {
          const isOut = t.type === "cash_out";
          return (
            <div
              key={t.id}
              className="px-4.5 py-3 flex items-center justify-between gap-3 border-b border-[#F5F6FA] last:border-b-0 text-[13px]"
            >
              <div className="flex items-center gap-3 min-w-0">
                <span
                  className={`w-[70px] text-center rounded-lg py-0.5 text-[11px] font-bold shrink-0 ${
                    isOut ? "bg-[#DCEFFB] text-[#0B5E8C]" : "bg-[#FBDCF3] text-[#9A1873]"
                  }`}
                >
                  {isOut ? "Cash-out" : "Cash-in"}
                </span>
                <span className="text-slate-500 text-[11.5px] font-bold tracking-wide uppercase shrink-0">
                  {providerLabel(t.provider)}
                </span>
                <span className="text-slate-400 text-xs truncate">{t.account_ref}</span>
              </div>
              <div className="flex items-center gap-4 shrink-0">
                <span className="font-bold tabular-nums">{formatBDT(t.amount)}</span>
                <span className="text-[11.5px] text-slate-400 w-14 text-right">{formatRelative(t.occurred_at)}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
