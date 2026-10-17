import copy
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if "storyboard_addon" not in sys.modules:
    spec = importlib.util.spec_from_file_location("storyboard_addon", ROOT / "__init__.py", submodule_search_locations=[str(ROOT)])
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

from storyboard_addon import service  # noqa: E402


def document():
    brief = json.loads((ROOT / "_vendor/examples/rainy-classroom.json").read_text(encoding="utf-8"))
    return service.engine.generate({"brief": brief, "provider": "demo"})


def direction_output(layout, assets=()):
    boundaries = []
    for boundary in layout.get("boundaries", []):
        state = copy.deepcopy(boundary["original_start_context"])
        for character in state["characters"]:
            character.update(position="Beside the seat", pose="Sitting upright", gaze="Toward the listener", emotion="Attentive")
        for prop in state["props"]:
            prop.update(english_name="Phone", position="On the seat")
        boundaries.append({"id": boundary["id"], "state": state})
    return {"warnings": [], "notes": [], "boundaries": boundaries,
        "handoffs": [{"id": h["id"], "bridge": "Continue the approved gesture and response.", "sound_bridge": "Keep the room ambience continuous."} for h in layout.get("handoffs", [])],
        "reference_notes": [{"label": a["label"], "note": ""} for a in assets],
        "clips": [{"id": clip["id"], "context": "A quiet classroom with consistent lighting.",
            "subject_definitions": "Preserve character identity.", "summary": "A restrained interaction.", "retention_analysis": "Preserve identity and clothing.",
            "shots": [{"id": shot["id"], "direction": "Follow the approved action with subtle expressions.", "pacing_weight": 1,
                "speech_cues": ["Begin with the approved response." for _ in shot["source"]["dialogue"]],
                "camera": {"size": "Medium shot", "angle": "Eye level", "movement": "Locked camera", "transition": "Cut on the reaction", "layout": "Character 1 on the left, Character 2 on the right."},
                "dialogue_language": "Korean", "deliveries": ["Very quietly" if line["delivery"] else "" for line in shot["source"]["dialogue"]]} for shot in clip["shots"]],
            "overall_soundscape": "Quiet room ambience.", "non_diegetic_music": "N/A"} for clip in layout["clips"]]}


def fake_ai(provider, model, system, user, schema):
    data = json.loads(user)
    return direction_output(data["plan"], data["references"])
