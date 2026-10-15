"""The single canonical per-case aggregation rule (preregistered decision D4).

D4 in `docs/decisions_log.md`, `docs/preregistration.md` and
`docs/preregistration_pivot.md` all specify the per-(model, case) decision as the
MODAL replicate decision with **ties broken toward `flag`**, with no reference to
the ground-truth case label.

Earlier revisions of this pipeline implemented "conservative" relative to whichever
indicator was being queried. That made the tie direction depend on the case label:
ties resolved to `no_flag` on legitimate cases (suppressing false positives) and to
`flag` on suspicious cases (suppressing misses). The suspicious branch matched D4;
the legitimate branch did not. Both directions favoured the model, and the rule used
information unavailable in deployment.

This module exists so that the rule has exactly ONE implementation. Do not reimplement
it; import it. Alternative tie policies live in `aggregation_sensitivity.py` and are
reported as sensitivity analyses, never as the primary rule.
"""
from __future__ import annotations

TIE_TO = "flag"          # preregistered D4 tie direction, label-independent
_VALID = ("flag", "no_flag")


def modal_decision(decisions) -> str | None:
    """Modal replicate decision. Ties resolve to TIE_TO. None if every call ERRORed."""
    valid = [d for d in decisions if d in _VALID]
    if not valid:
        return None
    n_flag = sum(1 for d in valid if d == "flag")
    if 2 * n_flag == len(valid):
        return TIE_TO
    return "flag" if 2 * n_flag > len(valid) else "no_flag"


def modal_indicator(decisions, want: str) -> int | None:
    """1 if the modal decision equals `want`, else 0; None if every call ERRORed."""
    m = modal_decision(decisions)
    return None if m is None else (1 if m == want else 0)


def modal_flag_from_votes(votes) -> int:
    """votes: iterable of 0/1 flag indicators -> 0/1 modal flag decision."""
    return 1 if modal_decision(["flag" if v else "no_flag" for v in votes]) == "flag" else 0
