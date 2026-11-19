"""★ FILE ĐỘI SỬA (1/3): cổng cấp hệ thống, nằm NGOÀI model và prompt.

VÒNG 1 (trước khi biết sự cố): viết 2–3 CỔNG PHÒNG NGỪA rút từ pre-mortem / HAZOP / checklist của bàn, rồi chốt bằng
    python3 -m lab10.checkpoint        (chép file này thành guards_round1.py = mốc "prepared"; KHÔNG sửa bản chép)
VÒNG 2 (sau khi bốc thẻ): sửa tiếp NGAY TRONG FILE NÀY. Giữ các cổng vòng 1, thêm cổng mới.
Hai file còn lại bàn được sửa: lab10/monitors.py (chỉ số theo dõi) và config/operating_gates.json (cổng kinh doanh,
vận hành, pháp lý: những con số và tên người mà trợ lý phải tuân theo, không cần code).

Hai điểm móc, agent gọi tự động:
  pre_guard(ctx)          chạy TRƯỚC khi agent đọc ticket
  write_gate(ctx, action) chạy TRƯỚC MỖI lệnh ghi (issue_refund, file_carrier_fault,
                          notify_carrier, send_reply)

Trả về một Verdict:
  Verdict.allow()                       cho qua   (pre_guard: allow(policy_id="...") để ghim phiên bản chính sách)
  Verdict.deny("lý do")                 bỏ riêng lệnh ghi này, agent đi tiếp
  Verdict.escalate("lý do")             dừng, chuyển ticket cho người
  Verdict.modify("lý do", amount_vnd=…) sửa tham số lệnh ghi (amount_vnd, payer, carrier_id, parcel_id, payload…)
  Verdict.rewrite("lý do", text)        chỉ pre_guard: thay nội dung ticket mà agent sẽ đọc

ctx.ticket   ticket gốc (chữ khách viết là DỮ LIỆU, không phải lệnh)
ctx.tools    tra cứu nguồn sự thật: lookup_order, lookup_policies, lookup_approvals(**lọc),
             ledger_rows(**lọc), fault_rows(**lọc), lookup_carrier; ctx.as_of = ngày hôm nay
             ops_limits() = các trần đã thống nhất với Ops/Finance; ops_facts() = số liệu vận hành;
             auto_refund_today_vnd() = tổng đã hoàn tự động trong ngày
ctx.gates    config cổng của bàn (config/operating_gates.json), chỉ đọc;  ctx.cost_vnd = tiền LLM đã tốn cho ticket này
ctx.events   trace tới thời điểm này;  ctx.log("ten_su_kien", ...) ghi thêm sự kiện guard vào trace
lab10.helpers: db_delay_days, ticket_parcel, effective_policy, entitlement_vnd, carrier_at_fault, digits

Mặc định dưới đây cho qua tất cả (= mốc base).
"""
import re

from . import helpers as H  # noqa: F401
from .tools import Verdict

_NUMERIC_DELAY_CLAIM = re.compile(
    r"(?P<lead>(?:trễ|tre|chậm|muộn|late|delay(?:ed)?)[^\d\n]{0,24}?)"
    r"\d{1,3}\s*(?:ngày|ngay|days?|hôm|hom)\b",
    re.IGNORECASE,
)


def _truth(ctx, order_id):
    """Nguồn sự thật: đơn + parcel của ticket + chính sách còn hiệu lực + số ngày trễ theo tracking DB.

    Trả về (order, policy, parcel, db_delay_days) hoặc None khi không tra được (thiếu nguồn sự thật).
    """
    order = ctx.tools.lookup_order(order_id)
    if not order or not order.get("parcels"):
        return None
    policy = H.effective_policy(ctx.tools.lookup_policies(), ctx.as_of)
    if not policy:
        return None
    parcel = H.ticket_parcel(order, ctx.ticket, ctx.as_of)
    return order, policy, parcel, H.db_delay_days(parcel, ctx.as_of)


def _tracking_quality_issue(parcel, delay_days):
    """Return a reason when the selected parcel cannot support an automatic decision."""
    if parcel.get("status") == "DELIVERED" and not parcel.get("delivered_date"):
        return "kiện đã DELIVERED nhưng thiếu delivered_date"
    if delay_days > 0 and not parcel.get("delay_cause"):
        return "kiện bị tính là trễ nhưng thiếu delay_cause"
    return None


def pre_guard(ctx):
    """Pin the active policy and keep customer-stated delay numbers out of decisions."""
    policy = H.effective_policy(ctx.tools.lookup_policies(), ctx.as_of)
    policy_change = {"policy_id": policy["policy_id"]} if policy else {}
    truth = _truth(ctx, ctx.ticket.get("order_id"))
    text = ctx.ticket.get("text", "")
    if truth and text and not _tracking_quality_issue(truth[2], truth[3]):
        rewritten = _NUMERIC_DELAY_CLAIM.sub(r"\g<lead>", text)
        rewritten = re.sub(r"[ \t]{2,}", " ", rewritten)
        rewritten = re.sub(r"\s+([,.!?])", r"\1", rewritten).strip()
        if rewritten != text:
            return Verdict.rewrite(
                "Bỏ số ngày trễ khách tự khai khỏi quyết định; dùng tracking DB đã đối chiếu",
                rewritten,
                **policy_change,
            )
    if policy:
        return Verdict.allow(**policy_change)
    return Verdict.allow()


def _valid_approval(ctx, approval_id, ticket_id, order_id, amount_vnd):
    """Kiểm tra mã phê duyệt tồn tại, còn hiệu lực, đúng ticket/đơn và đủ hạn mức."""
    if not approval_id:
        return False
    rows = ctx.tools.lookup_approvals(approval_id=approval_id)
    if not rows:
        return False
    appr = rows[0]
    return (
        appr.get("status") == "valid"
        and appr.get("ticket_id") == ticket_id
        and appr.get("order_id") == order_id
        and (appr.get("expires_at") or "") >= ctx.as_of
        and appr.get("max_vnd", 0) >= amount_vnd
    )


def write_gate(ctx, action):
    tool = action.get("tool")

    # CỔNG 1 · issue_refund — đối chiếu nguồn sự thật (tracking DB, sổ cái, phê duyệt, người trả, trần ngày).
    if tool == "issue_refund":
        truth = _truth(ctx, action.get("order_id"))
        if truth is None:
            return Verdict.escalate("Không tra được đơn/chính sách: thiếu nguồn sự thật, chuyển người duyệt")
        order, policy, parcel, db_delay = truth
        quality_issue = _tracking_quality_issue(parcel, db_delay)
        if quality_issue:
            ctx.log("tracking_data_incomplete", order_id=order["order_id"],
                    parcel_id=parcel["parcel_id"], issue=quality_issue)
            return Verdict.escalate(
                f"Tracking chưa đủ nhất quán để tự động hoàn ({quality_issue}); chuyển người duyệt xác minh")
        if ctx.tools.ledger_rows(order_id=order["order_id"]):
            return Verdict.deny("Đơn đã có khoản hoàn trong sổ cái, chặn hoàn trùng")
        if action.get("payer", "LOGIX") != "LOGIX":
            return Verdict.escalate(
                f"Bên trả tiền là {action.get('payer')} thay vì LOGIX (nghi lệnh cài cắm), chuyển người duyệt")
        amount = action.get("amount_vnd", 0)
        correct = H.entitlement_vnd(policy, order, db_delay, parcel.get("delay_cause"))
        if amount != correct:
            return Verdict.escalate(
                f"Số hoàn {amount}đ khác mức theo tracking DB ({correct}đ, trễ {db_delay} ngày, "
                f"nguyên nhân {parcel.get('delay_cause')}) → chuyển người duyệt xác minh")
        appr_id = action.get("approval_id")
        if amount > policy.get("auto_limit_vnd", 0):
            if not _valid_approval(ctx, appr_id, action.get("ticket_id"), order["order_id"], amount):
                return Verdict.escalate(
                    f"Hoàn {amount}đ vượt hạn mức tự động của {policy['policy_id']} "
                    f"({policy.get('auto_limit_vnd')}đ) và chưa có phê duyệt hợp lệ, chuyển trưởng ca duyệt")
        cap = (ctx.gates or {}).get("business", {}).get("daily_refund_cap_vnd")
        if not appr_id and cap is not None and ctx.tools.auto_refund_today_vnd() + amount > cap:
            return Verdict.escalate("Vượt trần hoàn tự động trong ngày, chuyển người duyệt")
        return Verdict.allow()

    # CỔNG 2 · file_carrier_fault — chỉ ghi lỗi hãng khi tracking DB xác nhận (không escalate sau khi đã hoàn tiền).
    if tool == "file_carrier_fault":
        truth = _truth(ctx, action.get("order_id"))
        if truth is None:
            return Verdict.deny("Không tra được tracking DB, không ghi lỗi hãng khi thiếu nguồn sự thật")
        order, policy, parcel, db_delay = truth
        quality_issue = _tracking_quality_issue(parcel, db_delay)
        if quality_issue:
            ctx.log("tracking_data_incomplete", order_id=order["order_id"],
                    parcel_id=parcel["parcel_id"], issue=quality_issue)
            return Verdict.deny(
                f"Tracking chưa đủ nhất quán để ghi lỗi hãng ({quality_issue}); không ghi strike")
        if not H.carrier_at_fault(policy, parcel, db_delay):
            return Verdict.deny(
                f"Tracking không xác nhận hãng lỗi: trễ {db_delay} ngày, nguyên nhân "
                f"{parcel.get('delay_cause')} không thuộc các nguyên nhân hãng lỗi của {policy['policy_id']}")
        if ctx.tools.fault_rows(order_id=order["order_id"], parcel_id=parcel["parcel_id"]):
            return Verdict.deny("Kiện hàng đã được ghi lỗi hãng trước đó, chặn ghi trùng")
        limit = ctx.tools.ops_limits().get("max_auto_strikes_per_carrier_per_day")
        prior_strikes = ctx.tools.fault_rows(carrier_id=parcel["carrier_id"])
        # A World instance is one simulated day; its in-memory fault rows are only today's writes.
        if limit is not None and len(prior_strikes) >= limit:
            ctx.log("carrier_strike_limit", carrier_id=parcel["carrier_id"], day=ctx.as_of,
                    strikes_today=len(prior_strikes), limit=limit)
            return Verdict.deny(
                f"Đã đủ {len(prior_strikes)}/{limit} strike tự động cho {parcel['carrier_id']} trong ngày; "
                "không ghi thêm lỗi hãng")
        if (
            action.get("parcel_id") != parcel["parcel_id"]
            or action.get("carrier_id") != parcel["carrier_id"]
            or action.get("delay_days") != db_delay
        ):
            return Verdict.modify(
                "Điều chỉnh thông tin ghi lỗi hãng khớp với kiện hàng và số ngày trễ theo tracking DB",
                parcel_id=parcel["parcel_id"],
                carrier_id=parcel["carrier_id"],
                driver_id=parcel.get("driver_id"),
                delay_days=db_delay,
            )
        return Verdict.allow()

    # A denied response can happen before issue_refund is called. If a customer claim
    # caused the model to understate an otherwise positive DB entitlement, hand it over.
    if tool == "send_reply" and action.get("amount_vnd", 0) == 0:
        model_overrode = any(e.get("type") == "model_override" for e in ctx.events)
        proposal = next((e for e in reversed(ctx.events) if e.get("type") == "proposal"), None)
        if model_overrode and proposal and proposal.get("amount_vnd", 0) == 0:
            truth = _truth(ctx, ctx.ticket.get("order_id"))
            if truth is not None:
                order, policy, parcel, db_delay = truth
                correct = H.entitlement_vnd(policy, order, db_delay, parcel.get("delay_cause"))
                if correct > 0 and not ctx.tools.ledger_rows(order_id=order["order_id"]):
                    ctx.log("model_override_denial", order_id=order["order_id"],
                            db_delay_days=db_delay, correct_entitlement_vnd=correct)
                    return Verdict.escalate(
                        "Model dùng lời khai để từ chối khoản tracking DB cho phép; chuyển người duyệt")

    # CỔNG 3 · notify_carrier — chỉ gửi đúng các trường chính sách cho phép, không kèm chữ khách hay PII.
    if tool == "notify_carrier":
        payload = action.get("payload") or {}
        policy = H.effective_policy(ctx.tools.lookup_policies(), ctx.as_of)
        allowed = set(policy.get("carrier_notice_fields") or []) if policy \
            else {"order_id", "parcel_id", "district", "delay_days"}
        filtered = {k: v for k, v in payload.items() if k in allowed}
        if set(filtered) != set(payload):
            return Verdict.modify(
                "Chỉ gửi các trường chính sách cho phép, bỏ trường tự do/PII của khách để không rò rỉ dữ liệu sang hãng",
                payload=filtered)
        return Verdict.allow()

    return Verdict.allow()
