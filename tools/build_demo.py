"""Build an allowlisted static sample site; never read settings or call an AI."""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / '_vendor'))

from clip_snapshot import make_bundle  # noqa: E402
from storyboard import conversion, engine, guides, prompt_renderer  # noqa: E402

ASSETS = ('index.html', 'demo.css', 'demo.js', 'workflow.js')
GUIDES = ('minimax-h3-text', 'seedance-2-text', 'ltx-2.5-text')


def authored_directions(layout, english):
    source = {s['id']: s for s in english['story']['shots']}
    return {'clips': [{
        'id': c['id'], 'context': 'A classroom after school. Gentle rain and warm late-afternoon window light. '
            'Haru has short dark hair and a navy uniform; Yuna has long dark hair and a navy uniform. '
            'Keep Haru near the window and Yuna beside the adjacent desk until they leave together.',
        'subject_definitions': 'Haru [haru] is reserved and thoughtful. Yuna [yuna] is observant and considerate.',
        'summary': 'Haru hesitates; Yuna offers to share her umbrella and walk home together.',
        'retention_analysis': 'Maintain the approved identities, uniforms, classroom layout and clear umbrella.',
        'shots': [{'id': s['id'], 'direction': source[s['id']]['visual'] + ' ' + ' '.join(source[s['id']]['actions']),
            'pacing_weight': 1, 'camera': {**source[s['id']]['camera'],
                'layout': 'Keep the established window and adjacent desks coherent. '
                    'Frame the approved acting subject without reversing the conversation axis.'},
            'dialogue_language': 'English',
            'deliveries': [source[s['id']]['dialogue'][i]['delivery'] if d['delivery'] else ''
                           for i, d in enumerate(s['source']['dialogue'])],
            'speech_cues': [{'speaker': d['speaker'], 'mode': 'unspecified',
                'onset': 'Begin the assigned line with the approved gesture or response.'}
                for d in s['source']['dialogue']]} for s in c['shots']],
        'overall_soundscape': 'Soft rain against the classroom window and quiet footsteps.',
        'non_diegetic_music': 'N/A'} for c in layout['clips']],
        'boundaries': [], 'handoffs': [{'id': h['id'],
            'bridge': 'Continue the established classroom conversation without replaying its opening.',
            'sound_bridge': 'Carry the same soft rain ambience across the connection.'}
            for h in layout.get('handoffs', [])], 'reference_notes': [], 'warnings': [], 'notes': []}


def build(destination):
    destination = Path(destination).resolve()
    if not destination.is_relative_to(ROOT / 'dist'):
        raise ValueError('Build only inside the ignored dist directory')
    destination.mkdir(parents=True, exist_ok=True)
    english = json.loads((ROOT / 'demo/samples/en.json').read_text(encoding='utf-8'))
    data = {'version': 1, 'engine_commit': json.loads((ROOT / '_vendor/upstream.json').read_text())['commit'],
            'sample_kind': 'Authored sample, not live AI output', 'samples': {}}
    for lang in ('en', 'ko', 'ja'):
        document = json.loads((ROOT / f'demo/samples/{lang}.json').read_text(encoding='utf-8'))
        engine.validate_document(document)
        variants = {}
        for guide_id in GUIDES:
            profile = guides.profile(guide_id)
            for limit in (10, 15):
                layout = conversion.plan(document, [s['id'] for s in document['story']['shots']],
                                         limit=limit, split_mode='fixed')
                # Match preflight's integer video budgets and JS/Python snapshot hashes.
                for clip in layout['clips']:
                    clip['duration'] = int(clip['duration'])
                assert not layout['boundaries'], 'Sample cuts must not split inside a source shot'
                output, _ = prompt_renderer.assemble(document, layout, authored_directions(layout, english), profile, [])
                identity = hashlib.sha256(f'authored-demo:{lang}:{guide_id}:{limit}'.encode()).hexdigest()[:32]
                result = {'target_model': profile['target_model'], 'plan': layout, 'output': output,
                          'output_language': 'english_except_dialogue'}
                bundle = make_bundle(hashlib.sha256(('demo:' + lang).encode()).hexdigest()[:32], document, identity, result)
                variants[f'{guide_id}:{limit}'] = bundle
        data['samples'][lang] = {'document': document, 'variants': variants}
    for name in ASSETS:
        shutil.copyfile(ROOT / 'demo' / name, destination / name)
    (destination / 'data.json').write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    (destination / '.nojekyll').write_text('', encoding='utf-8')
    print('Built sample-only site:', destination, '(3 languages, 18 real-engine prompt bundles)')
    return copy.deepcopy(data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', default=str(ROOT / 'dist/site'))
    build(parser.parse_args().out)
