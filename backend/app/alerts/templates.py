"""Offline, template-based EN/BN narrative generation.

No external API calls: every string is built from evidence the analytics
layer already computed. Careful-language rule is enforced here in one place -
"unusual" / "requires review", never "fraud" - so it cannot be bypassed by a
future alert type forgetting to phrase things safely.
"""

from datetime import datetime

from app.analytics.anomaly import AnomalyResult
from app.analytics.forecaster import ForecastResult
from app.core.config import VELOCITY_WINDOW_MINUTES

_BN_DIGITS = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")
_BN_PROVIDER_NAMES = {"bkash": "বিকাশ", "nagad": "নগদ", "rocket": "রকেট"}


def to_bengali_digits(value: str) -> str:
    return value.translate(_BN_DIGITS)


def _period_word(hour: int) -> str:
    if 5 <= hour < 12:
        return "সকাল"
    if 12 <= hour < 16:
        return "দুপুর"
    if 16 <= hour < 19:
        return "বিকেল"
    if 19 <= hour < 22:
        return "সন্ধ্যা"
    return "রাত"


def bengali_time_phrase(dt: datetime) -> str:
    hour12 = dt.hour % 12 or 12
    phrase = f"{_period_word(dt.hour)} {to_bengali_digits(str(hour12))}টা"
    if dt.minute:
        phrase += f" {to_bengali_digits(str(dt.minute))} মিনিটে"
    return phrase


def bn_provider(provider_id: str, fallback: str) -> str:
    return _BN_PROVIDER_NAMES.get(provider_id, fallback)


def liquidity_messages(
    agent_name: str, forecast: ForecastResult, provider_names: dict[str, str]
) -> tuple[str, str, str]:
    title = f"{forecast.target_label} may run low"
    target_is_cash = forecast.target == "CASH"
    target_name_en = "shared cash reserve" if target_is_cash else forecast.target_label
    target_name_bn = "নগদ টাকা" if target_is_cash else f"{bn_provider(forecast.target, forecast.target_label)} ব্যালেন্স"

    top = forecast.top_contributors[0] if forecast.top_contributors else None
    top_name_en = provider_names.get(top["provider_id"], top["provider_id"]) if top else None

    if forecast.projected_shortage_at:
        time_en = forecast.projected_shortage_at.strftime("%I:%M %p").lstrip("0")
        message_en = f"At the current transaction pace, {target_name_en} for {agent_name} may run out around {time_en}. "
        if top_name_en:
            message_en += f"Most of the pressure is coming from {top_name_en} cash-out. "
        message_en += "Consider arranging additional cash or provider float in advance to keep serving customers safely."

        time_bn = bengali_time_phrase(forecast.projected_shortage_at)
        message_bn = f"বর্তমান লেনদেনের ধারা অনুযায়ী {time_bn}র মধ্যে {agent_name}-এর {target_name_bn} শেষ হয়ে যেতে পারে। "
        if top:
            message_bn += f"সবচেয়ে বেশি চাপ আসছে {bn_provider(top['provider_id'], top_name_en or top['provider_id'])} ক্যাশ-আউট থেকে। "
        message_bn += "নিরাপদভাবে সেবা চালু রাখতে অতিরিক্ত নগদ/ব্যালেন্স ব্যবস্থা করার পরামর্শ দেওয়া হচ্ছে।"
    else:
        message_en = f"{target_name_en.capitalize()} for {agent_name} needs attention; not enough data yet for a precise ETA."
        message_bn = f"{agent_name}-এর {target_name_bn} নিয়ে সতর্কতা প্রয়োজন। পর্যাপ্ত তথ্য পাওয়া গেলে সময় নির্দিষ্ট করা যাবে।"

    return title, message_en, message_bn


def stable_message(target_label: str, target: str) -> tuple[str, str]:
    en = f"{target_label} is stable based on the recent transaction pattern."
    bn_target = "নগদ টাকার পরিমাণ" if target == "CASH" else f"{bn_provider(target, target_label)} ব্যালেন্স"
    bn = f"সাম্প্রতিক লেনদেনের ধারা অনুযায়ী {bn_target} স্থিতিশীল রয়েছে।"
    return en, bn


def insufficient_data_message(target_label: str) -> tuple[str, str]:
    en = f"Not enough recent transaction data yet to forecast {target_label.lower()}."
    bn = f"{target_label} সম্পর্কে পূর্বাভাস দেওয়ার মতো পর্যাপ্ত সাম্প্রতিক তথ্য এখনও নেই।"
    return en, bn


def anomaly_messages(
    agent_name: str, provider_id: str, provider_name: str, anomaly: AnomalyResult
) -> tuple[str, str, str]:
    title = f"Unusual {provider_name} cash-out activity - requires review"
    message_en = (
        f"{anomaly.window_count} {provider_name} cash-out transactions happened in a short window at {agent_name}, "
        f"from only {anomaly.unique_customers} account(s), with amounts between {anomaly.amount_min:.0f} and "
        f"{anomaly.amount_max:.0f} BDT. This may be normal festival-time demand, but the transactions should be "
        "reviewed before approving a large cash replenishment. This is not a fraud determination."
    )
    message_bn = (
        f"গত {to_bengali_digits(str(VELOCITY_WINDOW_MINUTES))} মিনিটের ব্যবধানে {agent_name}-এ "
        f"{to_bengali_digits(str(anomaly.window_count))}টি {bn_provider(provider_id, provider_name)} ক্যাশ-আউট "
        f"লেনদেন হয়েছে, মাত্র {to_bengali_digits(str(anomaly.unique_customers))}টি অ্যাকাউন্ট থেকে, পরিমাণগুলো "
        "কাছাকাছি। এটি ঈদ-পূর্ব স্বাভাবিক চাহিদাও হতে পারে, তবে বড় অঙ্কের নগদ পুনরায় সরবরাহের আগে "
        "লেনদেনগুলো পর্যালোচনা করা প্রয়োজন। এটি জালিয়াতির প্রমাণ নয়।"
    )
    return title, message_en, message_bn


def data_quality_messages(agent_name: str, provider_id: str, provider_name: str) -> tuple[str, str, str]:
    title = f"{provider_name} data feed delayed"
    message_en = (
        f"The {provider_name} balance feed for {agent_name} has not updated recently. Liquidity estimates for "
        "this provider are shown with lower confidence until the feed is healthy again."
    )
    message_bn = (
        f"{agent_name}-এর {bn_provider(provider_id, provider_name)} ডেটা ফিড সাম্প্রতিক সময়ে আপডেট হয়নি। "
        "ফিড সুস্থ না হওয়া পর্যন্ত এই প্রোভাইডারের হিসাব কম নির্ভরযোগ্য হিসেবে দেখানো হচ্ছে।"
    )
    return title, message_en, message_bn
