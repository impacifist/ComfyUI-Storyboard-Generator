"""Versioned, locally reviewed official-guide profiles; no runtime scraping."""

import hashlib
from pathlib import Path

from .schema import ValidationError

ROOT = Path(__file__).resolve().parent.parent / "docs" / "guides"
PROFILES = {
    "seedance-2-text": ("Seedance 2.0", "text", "seedance-2.0.md"),
    "seedance-2-reference": ("Seedance 2.0", "reference", "seedance-2.0.md"),
    "minimax-h3-text": ("MiniMax H3", "text", "minimax-h3.md"),
    "minimax-h3-reference": ("MiniMax H3", "reference", "minimax-h3.md"),
    "ltx-2.5-text": ("LTX 2.5", "text", "ltx-2.5.md"),
    "ltx-2.5-image": ("LTX 2.5", "image", "ltx-2.5.md"),
}


def scope_rules():
    return (ROOT / "conversion-scope.md").read_text(encoding="utf-8")


def assembly_rules():
    return ((ROOT / "dialogue-assembly.md").read_text(encoding="utf-8") + "\n\n" +
            (ROOT / "clip-flow.md").read_text(encoding="utf-8") + "\n\n" +
            (ROOT / "anime-direction.md").read_text(encoding="utf-8") + "\n\n" +
            (ROOT / "action-causality.md").read_text(encoding="utf-8") + "\n\n" +
            (ROOT / "reference-roles.md").read_text(encoding="utf-8") + "\n\n" +
            (ROOT / "camera-techniques.ko.md").read_text(encoding="utf-8"))


def profile(key):
    if not isinstance(key, str) or key not in PROFILES:
        raise ValidationError("지원하는 공식 가이드를 선택해주세요.")
    target, mode, filename = PROFILES[key]
    guide = (ROOT / filename).read_text(encoding="utf-8")
    system = (ROOT / "compiler-system.md").read_text(encoding="utf-8").split("\n", 2)[2]
    if key.startswith("ltx"):
        sections = []
        system += "\n" + (ROOT / "ltx-system.md").read_text(encoding="utf-8")
        if mode == "image":
            system += ("\nIMAGE-TO-VIDEO: The user supplies each clip's opening frame in the video workflow. "
                       "No image has been analyzed here. Focus on approved motion, camera and audio starting "
                       "from that frame. Do not invent its visual contents or attachment labels. "
                       "Retain intentional source cuts; never add a cut merely because a clip starts.")
    elif key.startswith("seedance"):
        system += "\nUse Image N attachment labels. Describe camera, actions and continuity. " \
                  "The renderer supplies {dialogue}; you may describe <sound effects> and (music) without spoken words."
        sections = []
    else:
        sections = (["subject_definitions", "summary", "retention_analysis", "detailed_description"]
                    if mode == "reference" else ["integrated_multimodal_description"])
        sections += ["overall_soundscape", "non_diegetic_music"]
        system += "\nThe renderer supplies these section headings in order: " + ", ".join(sections)
        system += (". Write descriptions in English; do not output dialogue tags, speaker markers or headings. "
                   "The renderer inserts original-language dialogue and assigns speakers by vocal appearance. "
                   "Separate ambient sound from non-diegetic music; N/A if absent.")
        if mode == "reference":
            system += (" Use the exact Subject labels in character_bindings; never renumber them by appearance or reference order. "
                       "Define <Subject N> once per character and associate its character-reference <Picture N> assets. "
                       "Environment references describe locations and must not be assigned to a character Subject. "
                       "Use attachment tokens exactly as <Picture 1>, <Picture 2>, etc. everywhere, including "
                       "subject_definitions, retention_analysis and reference notes; never use Image N. "
                       "Retention analysis must state which identity/style attributes to preserve from each asset.")
        system += "\n" + (ROOT / "minimax-animation-direction.md").read_text(encoding="utf-8")
    system += "\n" + scope_rules()
    system += "\n" + assembly_rules()
    return {"id": key, "target_model": target, "mode": mode, "guide": guide,
            "guide_source": "\n".join(line[2:] for line in guide.splitlines() if line.startswith("- https://")),
            "system_prompt": system, "checked_at": ("2026-10-18" if key.startswith("ltx") else
                "2026-10-11" if key.startswith("minimax") else "2026-10-10"),
            "min_seconds": 4, "max_seconds": 15,
            "max_images": 9 if mode == "reference" else 0, "sections": sections,
            "sha256": hashlib.sha256((guide + system).encode()).hexdigest()}


def catalog():
    return [profile(key) for key in PROFILES]
