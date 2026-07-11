"""Builds the bilingual (English / Bangla / Banglish) title+message shown on
an alert, directly from the same evidence numbers the forecast/anomaly
services already compute - no LLM call (Phase 8, not built yet; this stays
rule-based/templated so it works with zero external dependency). Language is
deliberately advisory throughout: "unusual", "requires review" - never
"fraud" or "confirmed", per the brief's risk-interpretation rule.
"""

from app.agents import PROVIDER_DISPLAY_NAME, PROVIDER_DISPLAY_NAME_BN
from app.services.anomaly import AmountOutlierResult, AnomalyResult
from app.services.forecast import ForecastResult


def _provider_bn(provider_id: str) -> str:
    return PROVIDER_DISPLAY_NAME_BN.get(provider_id, provider_id)


def _provider_en(provider_id: str) -> str:
    return PROVIDER_DISPLAY_NAME.get(provider_id, provider_id)


def liquidity_narrative(agent_name: str, forecast: ForecastResult) -> tuple[str, str, str, str]:
    target = "shared cash reserve" if forecast.target == "CASH" else f"{_provider_en(forecast.target)} balance"
    target_bn = "নগদ টাকা" if forecast.target == "CASH" else f"{_provider_bn(forecast.target)} ব্যালেন্স"
    eta = forecast.projected_shortage_at.strftime("%I:%M %p") if forecast.projected_shortage_at else "an uncertain time"
    minutes = f"{forecast.minutes_to_shortage:.0f}" if forecast.minutes_to_shortage is not None else "?"
    top = forecast.top_contributors[0]["provider"] if forecast.top_contributors else None
    top_en = _provider_en(top) if top else "recent cash-out activity"
    top_bn = _provider_bn(top) if top else "সাম্প্রতিক ক্যাশ-আউট"

    title = f"{agent_name}: {target} may run out around {eta}"

    en = (
        f"Based on the current transaction trend, {agent_name}'s {target} may run out around {eta} "
        f"(approximately {minutes} minutes). Most of the pressure is coming from {top_en}. Consider arranging "
        "additional cash or coordinating provider support to keep serving customers safely. This is an estimate, "
        "not a guarantee."
    )
    bn = (
        f"বর্তমান লেনদেনের ধারা অনুযায়ী {agent_name}-এর {target_bn} আনুমানিক {eta}-এর মধ্যে শেষ হয়ে যেতে পারে "
        f"(প্রায় {minutes} মিনিট)। সবচেয়ে বেশি চাপ আসছে {top_bn} থেকে। নিরাপদভাবে সেবা চালু রাখতে অতিরিক্ত নগদ বা "
        "প্রোভাইডার সাপোর্ট ব্যবস্থা করার পরামর্শ দেওয়া হচ্ছে। এটি একটি অনুমান, নিশ্চয়তা নয়।"
    )
    banglish = (
        f"Ei muhurte cholmaan lenden dhara onujayi {agent_name}-er {target} prai {eta}-er modhdhe shesh hoye "
        f"jete pare (~{minutes} minute). Sobcheye beshi chap ashche {top_en} theke. Nirapode seba cholu rakhte "
        "extra cash ba provider support babostha korar poramorsho deya hocche."
    )
    return title, en, bn, banglish


def anomaly_velocity_narrative(agent_name: str, provider_id: str, result: AnomalyResult) -> tuple[str, str, str, str]:
    provider_en = _provider_en(provider_id)
    provider_bn = _provider_bn(provider_id)
    title = f"{agent_name}: unusual {provider_en} cash-out burst requires review"

    en = result.message
    bn = (
        f"গত কয়েক মিনিটের ব্যবধানে {agent_name}-এর {provider_bn} থেকে অস্বাভাবিক হারে ক্যাশ-আউট হয়েছে "
        f"({result.window_count}টি লেনদেন)। এর মধ্যে মাত্র {result.unique_customers}টি অ্যাকাউন্ট থেকে বারবার "
        "অনুরোধ এসেছে। এটি স্বাভাবিক চাহিদাও হতে পারে (যেমন ঈদের আগে), তবে বড় অঙ্কের সিদ্ধান্তের আগে লেনদেনগুলো "
        "পর্যালোচনা করা প্রয়োজন। এটি জালিয়াতির প্রমাণ নয়।"
    )
    banglish = (
        f"Gato koyek minuter moddhe {agent_name}-er {provider_en}-e onek beshi cash-out hoyeche "
        f"({result.window_count}ta transaction), moshto {result.unique_customers}ta account theke. Eta normal Eid "
        "demand-o hote pare, kintu boro sidhanto neyar age review kora dorkar. Eta fraud-er proman na."
    )
    return title, en, bn, banglish


def amount_outlier_narrative(agent_name: str, provider_id: str, result: AmountOutlierResult) -> tuple[str, str, str, str]:
    provider_en = _provider_en(provider_id)
    provider_bn = _provider_bn(provider_id)
    title = f"{agent_name}: unusual {provider_en} transaction amount for this agent"

    en = result.message
    amount = f"{result.evaluated_amount:.0f}" if result.evaluated_amount is not None else "?"
    hist_mean = f"{result.historical_mean:.0f}" if result.historical_mean is not None else "?"
    bn = (
        f"{agent_name}-এর সাম্প্রতিক {provider_bn} লেনদেনের পরিমাণ ({amount} টাকা) এই এজেন্টের নিজস্ব ইতিহাসের "
        f"তুলনায় অস্বাভাবিক - তার সাধারণ গড় প্রায় {hist_mean} টাকা। এটি একটি বৈধ বড় লেনদেনও হতে পারে, তবে বড় "
        "সিদ্ধান্তের আগে পর্যালোচনা করা প্রয়োজন। এটি জালিয়াতির প্রমাণ নয়।"
    )
    banglish = (
        f"{agent_name}-er সাম্প্রতিক {provider_en} transaction ({amount} taka) tar nijer history-r tulonay "
        f"unusual - shadharon gor prai {hist_mean} taka. Eta boro legitimate transaction-o hote pare, tobe "
        "review kora dorkar."
    )
    return title, en, bn, banglish


def data_quality_narrative(agent_name: str, provider_id: str, sync_status: str, staleness_seconds: float) -> tuple[str, str, str, str]:
    provider_en = _provider_en(provider_id)
    provider_bn = _provider_bn(provider_id)
    title = f"{agent_name}: {provider_en} data feed is {sync_status}"

    en = (
        f"{provider_en}'s data feed for {agent_name} is currently '{sync_status}' "
        f"({staleness_seconds:.0f}s since last update). Any liquidity or anomaly estimate involving this provider "
        "should be treated as lower-confidence until the feed recovers - this is a data-quality issue, not a "
        "confirmed shortage or fraud."
    )
    bn = (
        f"{agent_name}-এর জন্য {provider_bn}-এর ডেটা ফিড বর্তমানে '{sync_status}' অবস্থায় আছে "
        f"({staleness_seconds:.0f} সেকেন্ড ধরে আপডেট হয়নি)। ফিড সুস্থ না হওয়া পর্যন্ত এই প্রোভাইডার সংক্রান্ত "
        "যেকোনো অনুমানকে কম নির্ভরযোগ্য হিসেবে বিবেচনা করা উচিত। এটি ডেটা সমস্যা, নিশ্চিত ঘাটতি বা জালিয়াতি নয়।"
    )
    banglish = (
        f"{agent_name}-er jonno {provider_en}-er data feed ekhon '{sync_status}' obosthay ache "
        f"({staleness_seconds:.0f}s dhore update hoyni). Feed thik na hoya porjonto ei provider-er je kono "
        "estimate-ke kom bhorosajogyo dhora uchit. Eta data problem, confirmed shortage ba fraud na."
    )
    return title, en, bn, banglish
