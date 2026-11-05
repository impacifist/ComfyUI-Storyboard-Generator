"""Inspectable logical LLM inputs; edits cannot relabel speech or clip identities."""

import copy
import hashlib
import json

from . import conversion_structure, providers
from .schema import TEXT, ValidationError, array, validate

ACTION_RULES = (
    "ACTION SCOPE: The full-story brief is context, not a list of actions to execute in every clip. "
    "For a source shot split into multiple segments, its unedited visual/actions describe the WHOLE "
    "source shot. They are not separate commands to replay or complete in every segment. Use source_offset "
    "and source_end to stage only the current portion. Do not pull a later shot's action into the current "
    "shot, finish a later segment early, or replay an earlier action. segment_instruction is the user's "
    "specific direction for this segment, when supplied. For action_scope=user_edited_segment, the edited "
    "source visual/actions/camera are approved specifically for this segment. Preserve assigned original "
    "speech and speakers; do not invent timing certainty where source actions have no timestamps."
)
SUFFIX = '\nSHOT IDENTITY CONTRACT: ' + conversion_structure.RULES + '\n' + ACTION_RULES


def effective_system(system):
    return system if system.endswith(SUFFIX) else system + SUFFIX


def record(trace, phase, system, user, schema):
    if trace is not None:
        item = {'phase': phase, 'system': system, 'user': copy.deepcopy(user),
                'schema': copy.deepcopy(schema), 'provider_system': providers.format_instruction(system, schema)}
        trace.append(item)
        return item
    return None


def fingerprint(system, user, schema, provider, model):
    return hashlib.sha256(json.dumps([system, user, schema, provider, model], sort_keys=True,
                                    ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def same(left, right):
    if type(left) in (int, float) and type(right) in (int, float):
        return left == right
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(same(left[k], right[k]) for k in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(same(a, b) for a, b in zip(left, right))
    return left == right


def apply_edit(system, user, schema, provider, model, edit):
    original_hash = fingerprint(effective_system(system), user, schema, provider, model)
    if edit is None:
        return effective_system(system), copy.deepcopy(user), original_hash
    if not isinstance(edit, dict) or set(edit) != {'fingerprint', 'system', 'user'}:
        raise ValidationError('LLM 요청 수정 형식이 올바르지 않습니다.')
    if edit['fingerprint'] != original_hash:
        raise ValidationError('콘티 또는 변환 조건이 바뀌었습니다. LLM 전송 내용에서 원본 요청을 다시 불러오세요.')
    if not isinstance(edit['system'], str) or not edit['system'].strip() or len(edit['system']) > 150000:
        raise ValidationError('시스템 프롬프트는 1~150,000자여야 합니다.')
    expected = copy.deepcopy(user)
    edited = edit['user']
    normalized = copy.deepcopy(edited)
    try:
        for key in ('title', 'location', 'time', 'atmosphere', 'situation', 'intent', 'ending', 'required', 'excluded', 'style'):
            value = edited['brief'][key]
            validate(value, TEXT, 'request.brief.' + key)
            expected['brief'][key] = value
        for ci, clip in enumerate(expected['plan']['clips']):
            for si, segment in enumerate(clip['shots']):
                other = edited['plan']['clips'][ci]['shots'][si]
                validate(other['segment_instruction'], TEXT, f'{clip["id"]}.{segment["id"]}.segment_instruction')
                segment['segment_instruction'] = other['segment_instruction']
                for key in ('visual', 'purpose', 'continuity', 'actions', 'camera'):
                    value = other['source'][key]
                    if key == 'camera':
                        if not isinstance(value, dict) or value.keys() != segment['source']['camera'].keys():
                            raise ValidationError('카메라 필드 구성이 올바르지 않습니다.')
                        for item in value.values():
                            validate(item, TEXT, 'request.camera')
                    else:
                        validate(value, array(TEXT) if key == 'actions' else TEXT, 'request.source.' + key)
                    segment['source'][key] = copy.deepcopy(value)
                before = user['plan']['clips'][ci]['shots'][si]['source']
                changed = any(not same(before[k], segment['source'][k]) for k in ('visual', 'purpose', 'continuity', 'actions', 'camera'))
                scope = 'user_edited_segment' if changed else segment['action_scope']
                if other['action_scope'] not in (segment['action_scope'], scope):
                    raise ValidationError('행동 적용 범위 값이 올바르지 않습니다.')
                segment['action_scope'] = scope
                normalized['plan']['clips'][ci]['shots'][si]['action_scope'] = scope
    except (KeyError, IndexError, TypeError):
        raise ValidationError('사용자 요청 JSON의 필드 구성이 올바르지 않습니다.') from None
    if not same(expected, normalized):
        raise ValidationError('컷·클립 ID, 시간, 원본 대사·화자, 상태·레퍼런스 연결은 변경할 수 없습니다. 구간 지시와 행동·화면·카메라 설명을 수정하세요.')
    return effective_system(edit['system']), expected, original_hash
