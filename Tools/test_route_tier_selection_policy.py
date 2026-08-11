#!/usr/bin/env python3
"""Guard that v1.1.244 wires the route-tier selection rule into the Swift
ExternalCandidate comparison.

The rule (same as Tools/route_selector.py): rank each candidate into a
readability tier — strict-readable > orientation-safe > unsafe — and let a
strictly safer tier dominate alpha, so a high-alpha but heavily inverted/
sideways/hard route can never beat a safe route.
"""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SWIFT = ROOT / "Sources" / "StickerNestMac.swift"


def main() -> int:
    source = SWIFT.read_text()

    required_markers = {
        '"1.1.244"': "app version bumped to 1.1.244",
        "STICKERNEST_EXTERNAL_ROUTE_TIER_SELECTION": "route-tier selection env gate",
        "routeTierSelectionEnabled": "route-tier selection enabled flag",
        "externalRouteSelectionTier": "shared route-tier helper",
        "candidateRouteTier": "candidate route tier computed",
        "bestRouteTier": "best candidate route tier computed",
        "isBlockedByRouteTier": "less-safe candidate is blocked by route tier",
        "isRouteTierUpgrade": "safer candidate upgrades by route tier",
        "external_auto_nest_candidate_rejected_by_route_tier_selection": "route-tier rejection log",
        "external_auto_nest_candidate_best_route_tier_upgrade": "route-tier upgrade log",
        "version_route_tier_selection_changed": "cache invalidation key",
        "externalRouteSelectionBetter": "same-tier alpha-first comparator helper",
        "isSameTierBetter": "same-tier preference used in isNewBest",
        "candidateAllowsPrimaryStop": "primary stop gated on strict tier",
        "external_auto_nest_primary_material_stop_held_for_strict_tier": "held-stop log when tier<strict",
        "version_route_tier_early_stop_changed": "early-stop cache invalidation key",
        # v1.1.244 near-strict direction rescue
        "STICKERNEST_EXTERNAL_ROUTE_NEAR_STRICT_SELECTION": "near-strict env gate",
        "routeNearStrictSelectionEnabled": "near-strict enabled flag",
        "externalRouteNearStrictOK": "near-strict predicate helper",
        "externalRouteSelectionReplaces": "tier+budget replace helper",
        "routeTierReplacesBest": "route-tier replace decision",
        "routeNearStrictAlphaBudget": "near-strict alpha-loss budget",
        "isNearStrictUpgrade": "near-strict-over-safe upgrade flag",
        "isRejectedByNearStrict": "safe-blocked-by-near-strict flag",
        "external_auto_nest_candidate_best_near_strict_upgrade": "near-strict upgrade log",
        "external_auto_nest_candidate_rejected_by_near_strict_selection": "near-strict rejection log",
        "version_route_near_strict_selection_changed": "near-strict cache invalidation key",
    }
    missing = [label for marker, label in required_markers.items() if marker not in source]
    if missing:
        print("missing route-tier selection markers: " + ", ".join(missing))
        return 1

    # The tier helper must define all four tiers strict(3)/near(2)/safe(1)/unsafe(0).
    helper_start = source.find("static func externalRouteSelectionTier")
    helper = source[helper_start: helper_start + 1100] if helper_start >= 0 else ""
    for token in ("return 3", "return 2", "return 1", "return 0"):
        if token not in helper:
            print(f"externalRouteSelectionTier must define {token} (strict/near/safe/unsafe)")
            return 1
    if "upside == 0" not in helper or "sideways == 0" not in helper or "hard == 0" not in helper:
        print("strict-readable tier must require zero upside/sideways/hard")
        return 1

    # The near-strict predicate must use readable/upside/sideways/hard thresholds and
    # the replace helper must apply the budget asymmetrically (loss<=budget to upgrade,
    # gain>budget to retake).
    if "STICKERNEST_EXTERNAL_NEAR_STRICT_MIN_READABLE" not in source:
        print("near-strict predicate must read a configurable min-readable threshold")
        return 1
    if "(bestAlpha - candidateAlpha) <= nearStrictAlphaBudget" not in source:
        print("near-strict over safe must require alpha loss within budget")
        return 1
    if "(candidateAlpha - bestAlpha) > nearStrictAlphaBudget" not in source:
        print("plain safe retaking near-strict must require alpha gain beyond budget")
        return 1

    # A less-safe candidate must be blocked regardless of alpha; the route-tier
    # block must feed into isNewBest.
    if "!isBlockedByRouteTier" not in source:
        print("isNewBest must exclude candidates blocked by a safer best tier")
        return 1

    # The safer-tier upgrade must bypass material-alpha protection (already keyed
    # on isOrientationSafeUpgrade, which now also covers a route-tier upgrade).
    if "|| isRouteTierUpgrade" not in source:
        print("route-tier upgrade must fold into the orientation-safe upgrade path")
        return 1

    # Same-tier decision must be alpha-first, not selectionScore-only. The final
    # isNewBest must route through isSameTierBetter, and that path must compare
    # alpha (highest material) before any tie-break.
    if "isOrientationSafeUpgrade || isSameTierBetter" not in source:
        print("isNewBest must use isSameTierBetter (alpha-first), not selectionScore alone")
        return 1

    # Guard against regressing to the old bare comparator inside isNewBest.
    if "isOrientationSafeUpgrade || candidate.selectionScore > bestCandidate!.selectionScore" in source:
        print("isNewBest must no longer decide same-tier purely on selectionScore")
        return 1

    # The comparator helper must prefer higher alpha first, then fall back to
    # bbox / target / selectionScore for stable tie-breaking.
    cmp_start = source.find("static func externalRouteSelectionBetter")
    cmp = source[cmp_start: cmp_start + 1200] if cmp_start >= 0 else ""
    if not cmp:
        print("missing externalRouteSelectionBetter helper")
        return 1
    if "candidateAlpha > bestAlpha" not in cmp:
        print("externalRouteSelectionBetter must prefer higher alpha first")
        return 1
    for token in ("candidateBBox > bestBBox", "candidateTarget > bestTarget", "candidateScore > bestScore"):
        if token not in cmp:
            print(f"externalRouteSelectionBetter must tie-break on {token}")
            return 1

    # The same-tier comparator must actually be wired with the candidate's alpha
    # and bbox coverage at the call site.
    if "candidateAlpha: candidate.alpha" not in source or "layoutBBoxCoverage(candidate.result)" not in source:
        print("isSameTierBetter must pass the candidate's alpha and bbox coverage")
        return 1

    # Early-stop tier gate (v1.1.244/233): a not-strict (tier<3) candidate must not be
    # allowed to fast-stop the primary target. The primary-material stop block must
    # be guarded by candidateAllowsPrimaryStop, defined from the route tier.
    if "candidateAllowsPrimaryStop = !routeTierSelectionEnabled || candidateRouteTier >= 3" not in source:
        print("candidateAllowsPrimaryStop must require strict tier3 when route-tier selection is on")
        return 1
    # The primary-material stop block must be gated by candidateAllowsPrimaryStop,
    # and the held branch must trigger when it is false (tier<2).
    if "candidateAllowsPrimaryStop," not in source:
        print("primary-material stop block must be gated by candidateAllowsPrimaryStop")
        return 1
    if "!candidateAllowsPrimaryStop," not in source:
        print("held-stop branch must fire when candidate is not strict tier (tier<3)")
        return 1

    # The pool must keep searching lower targets while the best is not strict (tier<3)
    # instead of stopping before lower targets.
    if "reason=best_tier_below_strict" not in source:
        print("pool must continue to lower targets while best tier < 3")
        return 1
    if "bestStrictTier < 3" not in source:
        print("stop-before-lower-targets must be gated on bestStrictTier >= 3")
        return 1

    print("PASS route-tier selection markers present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
