"""Fail-closed policy firewall between EVM preflight and the signer boundary.

The governor is deliberately execution-agnostic. It does not reserve nonces,
sign, submit, call an RPC, or consume replay state. It evaluates immutable
evidence supplied by the durable control plane and returns an auditable
decision. AI ranking is informational only and can never authorize execution.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from .economic_proof import EconomicProof
from .economics import STRICT_MIN_NET_PROFIT_USD
from .evm_preflight import EVMPreflightResult
from .execution import ExecutionIntent, ExecutionState, TransactionEnvelope
from .executor_authority import ExecutorAuthorityEvidence, ExecutorAuthorityError, verify_executor_authority
from .hashing import keccak256_hex


class GovernorError(ValueError):
    """Raised when governor policy configuration is invalid."""


def _decimal(value: Decimal | int | str, name: str) -> Decimal:
    try:
        parsed = Decimal(value)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise GovernorError(f"{name} is not a valid decimal") from exc
    if not parsed.is_finite():
        raise GovernorError(f"{name} must be finite")
    return parsed


def _hash(value: str, name: str) -> str:
    if not isinstance(value, str) or len(value) != 66 or not value.startswith("0x"):
        raise GovernorError(f"{name} must be a 32-byte 0x hash")
    try:
        int(value[2:], 16)
    except ValueError as exc:
        raise GovernorError(f"{name} must be hexadecimal") from exc
    return value.lower()


def _address(value: str, name: str) -> str:
    if not isinstance(value, str) or len(value) != 42 or not value.startswith("0x"):
        raise GovernorError(f"{name} must be a 20-byte 0x address")
    try:
        int(value[2:], 16)
    except ValueError as exc:
        raise GovernorError(f"{name} must be hexadecimal") from exc
    return value.lower()


@dataclass(frozen=True)
class GovernorPolicy:
    """Immutable execution policy; safe defaults keep live capital locked."""

    expected_chain_id: int = 137
    live_execution_enabled: bool = False
    max_block_drift: int = 2
    max_gas_limit: int = 1_500_000
    max_fee_per_gas: int = 10_000_000_000
    max_priority_fee_per_gas: int = 10_000_000_000
    max_gas_usd: Decimal = Decimal("1.00")
    max_relay_usd: Decimal = Decimal("1.00")
    minimum_net_profit_usd: Decimal = STRICT_MIN_NET_PROFIT_USD
    approved_executors: tuple[str, ...] = ()
    approved_senders: tuple[str, ...] = ()
    allowed_loan_assets: tuple[str, ...] = ()
    allowed_route_hashes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.expected_chain_id <= 0:
            raise GovernorError("expected chain id must be positive")
        if self.max_block_drift < 0:
            raise GovernorError("max block drift cannot be negative")
        if self.max_gas_limit <= 0:
            raise GovernorError("max gas limit must be positive")
        if self.max_fee_per_gas < 0 or self.max_priority_fee_per_gas < 0:
            raise GovernorError("gas fee ceilings cannot be negative")
        if self.max_fee_per_gas < self.max_priority_fee_per_gas:
            raise GovernorError("max fee ceiling must cover priority fee ceiling")
        for name in ("max_gas_usd", "max_relay_usd", "minimum_net_profit_usd"):
            value = _decimal(getattr(self, name), name)
            if value < 0:
                raise GovernorError(f"{name} cannot be negative")
            object.__setattr__(self, name, value)
        if self.minimum_net_profit_usd < STRICT_MIN_NET_PROFIT_USD:
            raise GovernorError("policy minimum cannot be below the canonical strict floor")
        object.__setattr__(self, "approved_executors", tuple(_address(x, "executor") for x in self.approved_executors))
        object.__setattr__(self, "approved_senders", tuple(_address(x, "sender") for x in self.approved_senders))
        object.__setattr__(self, "allowed_loan_assets", tuple(_address(x, "loan asset") for x in self.allowed_loan_assets))
        object.__setattr__(self, "allowed_route_hashes", tuple(_hash(x, "route hash") for x in self.allowed_route_hashes))


@dataclass(frozen=True)
class GovernorDecision:
    """Immutable, hashable audit evidence for the governor outcome."""

    approved: bool
    reason: str
    chain_id: int
    block_number: int
    intent_hash: str
    route_hash: str
    economic_proof_hash: str
    simulation_proof_hash: str
    calldata_hash: str
    executor_authority_hash: str
    ai_rank: str | None = None
    decision_hash: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.reason, str) or not self.reason:
            raise GovernorError("decision reason is required")
        for name in (
            "intent_hash",
            "route_hash",
            "economic_proof_hash",
            "simulation_proof_hash",
            "calldata_hash",
            "executor_authority_hash",
        ):
            object.__setattr__(self, name, _hash(getattr(self, name), name))
        expected = self._digest()
        if self.decision_hash:
            if self.decision_hash.lower() != expected:
                raise GovernorError("governor decision hash mismatch")
            object.__setattr__(self, "decision_hash", self.decision_hash.lower())
        else:
            object.__setattr__(self, "decision_hash", expected)

    def _digest(self) -> str:
        payload = {
            "approved": self.approved,
            "reason": self.reason,
            "chain_id": self.chain_id,
            "block_number": self.block_number,
            "intent_hash": self.intent_hash.lower(),
            "route_hash": self.route_hash.lower(),
            "economic_proof_hash": self.economic_proof_hash.lower(),
            "simulation_proof_hash": self.simulation_proof_hash.lower(),
            "calldata_hash": self.calldata_hash.lower(),
            "executor_authority_hash": self.executor_authority_hash.lower(),
            "ai_rank": self.ai_rank,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return keccak256_hex(encoded)


def govern_execution(
    *,
    policy: GovernorPolicy,
    preflight: EVMPreflightResult,
    intent: ExecutionIntent,
    envelope: TransactionEnvelope,
    economic_proof: EconomicProof,
    executor_authority: ExecutorAuthorityEvidence,
    lifecycle_state: ExecutionState,
    nonce_reserved: bool,
    replay_consumed: bool,
    current_block_number: int,
    now: int,
    ai_rank: Decimal | int | str | None = None,
) -> GovernorDecision:
    """Apply the final policy firewall without performing any external action.

    A blocked decision is returned as explicit audit evidence. No condition
    involving AI ranking can turn a policy failure into approval. The decision
    commits to the same authority evidence hash carried by preflight and
    revalidates that evidence against the exact execution identities.
    """
    rank_text: str | None
    if ai_rank is None:
        rank_text = None
    else:
        rank = _decimal(ai_rank, "ai_rank")
        rank_text = str(rank)

    authority_hash = _hash(executor_authority.evidence_hash, "executor authority hash")

    def block(reason: str) -> GovernorDecision:
        return GovernorDecision(
            approved=False,
            reason=reason,
            chain_id=preflight.chain_id,
            block_number=preflight.block_number,
            intent_hash=preflight.intent_hash,
            route_hash=preflight.route_hash,
            economic_proof_hash=preflight.economic_proof_hash,
            simulation_proof_hash=preflight.simulation_proof_hash,
            calldata_hash=preflight.calldata_hash,
            executor_authority_hash=authority_hash,
            ai_rank=rank_text,
        )

    if not preflight.passed:
        return block("preflight did not pass")
    if not policy.live_execution_enabled:
        return block("live execution is locked by policy")
    if lifecycle_state is not ExecutionState.VERIFIED:
        return block("execution must be exactly VERIFIED at governor boundary")
    if not nonce_reserved:
        return block("nonce reservation evidence is missing")
    if replay_consumed:
        return block("intent replay has already been consumed")
    if now < 0 or current_block_number < 0:
        return block("current time or block is invalid")
    if policy.expected_chain_id != 137:
        return block("production policy is restricted to Polygon chain 137")
    if preflight.chain_id != policy.expected_chain_id or intent.chain_id != policy.expected_chain_id or envelope.chain_id != policy.expected_chain_id:
        return block("chain identity does not match governor policy")
    if current_block_number < preflight.block_number:
        return block("current chain block is behind the proven simulation block")
    if current_block_number - preflight.block_number > policy.max_block_drift:
        return block("simulation block is outside the permitted block-drift window")
    if intent.deadline < now:
        return block("execution deadline has expired")

    if not preflight.authority_evidence_hash:
        return block("preflight authority evidence binding is missing")
    if preflight.authority_evidence_hash.lower() != authority_hash:
        return block("preflight authority evidence binding changed before governor")

    try:
        verify_executor_authority(
            executor_authority,
            chain_id=intent.chain_id,
            executor=intent.executor,
            sender=intent.sender,
            minimum_observed_block=preflight.block_number,
        )
    except ExecutorAuthorityError:
        return block("deployed executor authority evidence is invalid at governor boundary")

    if envelope.gas_limit > policy.max_gas_limit:
        return block("gas limit exceeds governor ceiling")
    if envelope.max_fee_per_gas > policy.max_fee_per_gas:
        return block("max fee per gas exceeds governor ceiling")
    if envelope.max_priority_fee_per_gas > policy.max_priority_fee_per_gas:
        return block("priority fee exceeds governor ceiling")
    if economic_proof.max_gas_usd > policy.max_gas_usd:
        return block("economic proof gas budget exceeds governor ceiling")
    if economic_proof.max_relay_usd > policy.max_relay_usd:
        return block("economic proof relay budget exceeds governor ceiling")
    if economic_proof.costs.gas > policy.max_gas_usd or economic_proof.costs.relay > policy.max_relay_usd:
        return block("bounded execution costs exceed governor ceiling")
    if economic_proof.minimum_net_profit_usd < policy.minimum_net_profit_usd:
        return block("economic proof minimum is below governor policy minimum")
    if economic_proof.worst_case_net_profit_usd <= policy.minimum_net_profit_usd:
        return block("worst-case net profit does not strictly exceed governor minimum")
    if intent.minimum_net_profit_usd != str(economic_proof.minimum_net_profit_usd):
        return block("intent profit floor is not bound to economic proof")
    if preflight.intent_hash.lower() != intent.intent_hash().lower():
        return block("preflight intent identity does not match current intent")
    if preflight.calldata_hash.lower() != envelope.calldata_hash.lower() or intent.calldata_hash.lower() != envelope.calldata_hash.lower():
        return block("calldata identity changed after preflight")
    if preflight.route_hash.lower() != intent.route_hash.lower():
        return block("route identity changed after preflight")
    if preflight.economic_proof_hash.lower() != economic_proof.proof_hash.lower() or intent.economic_proof_hash.lower() != economic_proof.proof_hash.lower():
        return block("economic proof identity changed after preflight")
    if preflight.simulation_proof_hash.lower() != intent.simulation_proof_hash.lower():
        return block("simulation proof identity changed after preflight")
    if not policy.approved_executors:
        return block("executor allowlist is not configured")
    if not policy.approved_senders:
        return block("sender allowlist is not configured")
    if not policy.allowed_loan_assets:
        return block("loan asset allowlist is not configured")
    if not policy.allowed_route_hashes:
        return block("route allowlist is not configured")
    if intent.executor.lower() not in policy.approved_executors:
        return block("executor is not allowlisted")
    if intent.sender.lower() not in policy.approved_senders:
        return block("sender is not allowlisted")
    if intent.loan_asset.lower() not in policy.allowed_loan_assets:
        return block("loan asset is not allowlisted")
    if intent.route_hash.lower() not in policy.allowed_route_hashes:
        return block("route is not allowlisted")

    return GovernorDecision(
        approved=True,
        reason="all governor policy gates passed",
        chain_id=preflight.chain_id,
        block_number=preflight.block_number,
        intent_hash=preflight.intent_hash,
        route_hash=preflight.route_hash,
        economic_proof_hash=preflight.economic_proof_hash,
        simulation_proof_hash=preflight.simulation_proof_hash,
        calldata_hash=preflight.calldata_hash,
        executor_authority_hash=authority_hash,
        ai_rank=rank_text,
    )
