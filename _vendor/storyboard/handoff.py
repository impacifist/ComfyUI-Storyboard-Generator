"""Directional scope guards, never free-form commands for a future action."""

from .schema import ValidationError

POLICY = (
    "CONNECTION OWNERSHIP: plan.handoffs is input metadata only. Do not return handoffs, bridge or "
    "sound_bridge fields. The application adds different incoming/outgoing scope rules. Each concrete "
    "movement belongs only to its assigned shot direction; clip context, summary, subject definitions, "
    "reference retention, audio and closing camera transition must not execute a later clip's action. "
    "Subject definitions and reference retention describe identity and appearance, not future behavior. "
    "An inherited state is already established, "
    "not an instruction to perform the establishing action again. Preserve approved cuts and scene changes."
)


def note(connection, side, *, prose=False):
    rules = {
        ('continuous_shot', 'incoming'): (
            "The opening frame already has the shared boundary state. Resume only the unfinished motion "
            "from that phase, within this clip's assigned source interval. Do not replay the movement "
            "that established the inherited state or restart the camera view."),
        ('continuous_shot', 'outgoing'): (
            "Let only this clip's assigned source interval reach the shared boundary state specified above. "
            "Leave the unfinished motion at that phase; do not execute actions reserved for a later interval. "
            "Preserve authored pauses, but add no settling pose, fade or countdown merely because this request ends."),
        ('planned_cut', 'incoming'): (
            "Start in the first listed shot's approved starting state and composition, after the planned cut. "
            "The previous clip has already reached its assigned end state; do not replay how it got there. "
            "Perform only this shot's assigned action, including a continuation only where the source calls for it. "
            "Let speech follow its assigned cue, not the generation boundary."),
        ('planned_cut', 'outgoing'): (
            "End at the last listed shot's own approved ending state and transition. Do not invent a lead-in "
            "or execute any action assigned to the next shot. Keep only anticipation and pauses already "
            "assigned to the current shot; add no fade or countdown merely because this request ends."),
        ('scene_change', 'incoming'): (
            "Use this scene's own approved location, time, starting state, composition and sound. "
            "Respect the scene transition without replaying actions from the previous scene."),
        ('scene_change', 'outgoing'): (
            "Complete only this scene's assigned action and approved ending transition. "
            "Leave the next scene's actions, setting and sound to its own clip."),
    }
    try:
        text = rules[(connection['kind'], side)]
        if prose:
            text = text.replace('the shared boundary state specified above', 'the described motion state')
            text = text.replace('the shared boundary state', 'the established motion state')
        return text
    except KeyError:
        raise ValidationError('지원하지 않는 클립 연결 유형입니다.') from None


def manifest(layout, *, prose=False):
    return [{'id': h['id'], 'kind': h['kind'], 'from_clip': h['from_clip'], 'to_clip': h['to_clip'],
             'outgoing': note(h, 'outgoing', prose=prose), 'incoming': note(h, 'incoming', prose=prose)}
            for h in layout.get('handoffs', [])]
