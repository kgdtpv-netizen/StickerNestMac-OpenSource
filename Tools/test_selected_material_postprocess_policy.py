#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SWIFT = ROOT / "Sources" / "StickerNestMac.swift"
AUTO_NEST = ROOT / "Tools" / "auto_nest.py"
BUILD = ROOT / "build.zsh"


def missing(markers: dict[str, str], source: str) -> list[str]:
    return [label for marker, label in markers.items() if marker not in source]


def main() -> int:
    swift = SWIFT.read_text()
    python = AUTO_NEST.read_text()
    build = BUILD.read_text()

    problems = missing(
        {
            'static let version = "1.1.244"': "AppInfo version should be bumped",
            'static let build = "20260607.005"': "AppInfo build should be bumped",
            "outputURL: URL": "external candidate should remember its JSON path",
            "STICKERNEST_POLISH_BASE_JSON": "Swift should pass selected JSON to Python",
            "bestCandidate.outputURL.path": "selected topup should use the selected candidate JSON",
            "external_auto_nest_selected_material_topup_postprocess": "Swift should log postprocess mode",
            "version_selected_material_postprocess_changed": "cache invalidation key",
        },
        swift,
    )
    if 'marketing_version="1.1.244"' not in build:
        problems.append("build.zsh marketing version should be bumped")
    problems.extend(
        missing(
            {
                "POLISH_BASE_JSON": "Python polish-base env variable",
                'os.environ.get("STICKERNEST_POLISH_BASE_JSON"': "Python polish-base env gate",
                "def load_polish_base_layout": "Python should load selected layout JSON",
                "normalized_name_to_index": "Python should match app-exported 000_ name prefixes",
                're.sub(r"^\\d{3}_"': "Python should strip app-export prefixes for selected-layout mapping",
                "polish_base_layout_used": "Python should log selected-layout mode",
                "material_alpha_topup(polish_base_layout": "Python should run material topup on the selected layout",
                "multi_piece_material_topup(polish_candidate": "Python should run multi-piece topup after material topup",
                "if POLISH_BASE_JSON": "Python should skip full search when selected JSON is provided",
                "if bestpl is not None and not POLISH_BASE_JSON": "normal broad postprocess should be disabled in selected-layout mode",
            },
            python,
        )
    )
    if problems:
        print("missing selected material postprocess markers: " + ", ".join(problems))
        return 1

    search_pos = python.find("best=-1e9")
    skip_pos = python.find("if not POLISH_BASE_JSON", search_pos)
    material_pos = python.find("def material_alpha_topup")
    load_pos = python.find("def load_polish_base_layout", material_pos)
    use_pos = python.find("if POLISH_BASE_JSON", load_pos)
    normal_post_pos = python.find("if bestpl is not None and not POLISH_BASE_JSON", use_pos)
    if min(search_pos, skip_pos, material_pos, load_pos, use_pos, normal_post_pos) < 0:
        print("missing selected-layout mode ordering markers")
        return 1
    if not (search_pos < skip_pos < material_pos < load_pos < use_pos < normal_post_pos):
        print("selected-layout mode should skip full search, then load and topup after topup functions are defined")
        return 1

    python_use_block = python[use_pos:normal_post_pos]
    for marker, label in {
        "polish_base_alpha": "base alpha should be measured before topup",
        "polish_candidate=material_alpha_topup(polish_base_layout": "material topup should start from selected layout",
        "polish_candidate=multi_piece_material_topup(polish_candidate": "multi-piece topup should continue from selected layout",
        "bestpl=polish_candidate": "export should use the postprocessed selected layout",
        "bestInk=ink(bestpl)": "exported metrics should be refreshed",
    }.items():
        if marker not in python_use_block:
            print("missing selected-layout Python guard: " + label)
            return 1

    env_pos = swift.find("STICKERNEST_SELECTED_MATERIAL_TOPUP_RUN")
    run_pos = swift.find("try process.run()", env_pos)
    if min(env_pos, run_pos) < 0:
        print("missing Swift selected topup process block")
        return 1
    env_block = swift[env_pos:run_pos]
    if 'environment["STICKERNEST_POLISH_BASE_JSON"] = bestCandidate.outputURL.path' not in env_block:
        print("Swift selected topup must pass the selected candidate JSON path")
        return 1
    if (
        'environment["STICKERNEST_LOCAL_ADAPTER"] = "0"' not in env_block
        or 'environment["STICKERNEST_STRUCTURAL_MICRO_GROW"] = "0"' not in env_block
        or 'environment["STICKERNEST_SCALE_TRANSFER"] = "0"' not in env_block
        or 'environment["STICKERNEST_SMALL_GROUP_MATERIAL_REPACK"] = "0"' not in env_block
    ):
        print("selected-layout topup must keep heavier repackers disabled")
        return 1

    cache_pos = swift.find("version_selected_material_postprocess_changed")
    previous_cache_pos = swift.find("version_selected_material_topup_changed")
    if min(cache_pos, previous_cache_pos) < 0:
        print("missing selected material postprocess cache ordering")
        return 1
    if not (cache_pos < previous_cache_pos):
        print("postprocess cache invalidation should run before v1.1.214 selected-topup invalidation")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
