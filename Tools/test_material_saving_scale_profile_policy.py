#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SWIFT = ROOT / "Sources" / "StickerNestMac.swift"
BUILD = ROOT / "build.zsh"


def require(source: str, marker: str, label: str) -> bool:
    if marker not in source:
        print(f"missing {label}: {marker}")
        return False
    return True


def main() -> int:
    swift = SWIFT.read_text()
    build = BUILD.read_text()
    ok = True

    required = {
        'static let version = "1.1.244"': "Swift app version",
        'static let build = "20260607.005"': "Swift app build",
        'marketing_version="1.1.244"': "bundle marketing version",
        "STICKERNEST_EXTERNAL_MATERIAL_SAVING_SCALE_PROFILE": "scale profile env gate",
        "materialSavingScaleProfileEnabled": "bounded scale profile flag",
        "struct MaterialSavingScaleProfile": "scale profile metadata",
        "let visualMin: Double": "scale profile visual minimum",
        "let materialSavingSeedScaleProfiles": "seed-to-profile map",
        "let materialSavingAttemptSeeds = materialSavingScaleProfileEnabled ? [4, 3] : [4]": "material-saving seed ladder should include profiled seed 3",
        "let visualBalanceMin: Double?": "attempt seed should carry optional visual min override",
        "visualBalanceMin: materialSavingSeedScaleProfiles[seed]?.visualMin": "material-saving seed should receive profile metadata",
        'environment["STICKERNEST_VISUAL_BALANCE_MIN"]': "attempt should pass visual min override to Python",
        'environment["STICKERNEST_VISUAL_BALANCE_POWER"]': "attempt should pin visual power with the profile",
        'environment["STICKERNEST_VISUAL_BALANCE_MAX"]': "attempt should pin visual max with the profile",
        "materialSavingScaleProfile": "attempt log should expose scale profile",
        "version_material_saving_scale_profile_changed": "cache invalidation key",
    }
    for marker, label in required.items():
        ok &= require(swift + build, marker, label)

    seed4 = swift.find("let materialSavingAttemptSeeds = materialSavingScaleProfileEnabled ? [4, 3] : [4]")
    append_profile = swift.find("visualBalanceMin: materialSavingSeedScaleProfiles[seed]?.visualMin")
    env_min = swift.find('environment["STICKERNEST_VISUAL_BALANCE_MIN"]')
    process_run = swift.find("try process.run()", env_min)
    if min(seed4, append_profile, env_min, process_run) < 0:
        print("missing material-saving scale-profile ordering markers")
        ok = False
    elif not (seed4 < append_profile < env_min < process_run):
        print("scale profile must be assigned to the attempt before launching auto_nest.py")
        ok = False

    cache_new = swift.find("version_material_saving_scale_profile_changed")
    cache_prev = swift.find("version_material_saving_low_alpha_stage_stop_changed")
    if min(cache_new, cache_prev) < 0:
        print("missing cache invalidation ordering markers")
        ok = False
    elif not (cache_new < cache_prev):
        print("scale-profile cache invalidation should run before v1.1.244 material-saving cache checks")
        ok = False

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
