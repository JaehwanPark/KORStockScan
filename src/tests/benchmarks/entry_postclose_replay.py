"""Offline replay benchmark for a frozen JSON sample; no provider or publication.

Run with the project Python and an explicit workspace and input artifact.
"""

import argparse
import hashlib
import json
from pathlib import Path
import resource
import sys
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace', required=True)
    parser.add_argument('--input', required=True)
    parser.add_argument('--version', choices=('baseline', 'new'), required=True)
    parser.add_argument('--family', choices=('machine', 'auxiliary'), required=True)
    args = parser.parse_args()
    output = sys.stdout
    sys.stdout = sys.stderr
    sys.path.insert(0, str(Path(args.workspace).resolve()))
    from src.engine.scalping import ai_action_outcome_calibration as calibration
    from src.engine.scalping import compact_auxiliary_paired_replay as compact
    if args.version == 'new':
        from src.engine.scalping import postclose_entry_validation as validation
        # Historical sources are a regression/benchmark, never a forward policy.
        validation.NEW_LOGIC_SOURCE_DATE = '2026-09-29'
    sample = json.loads(Path(args.input).read_text())
    code_sha256 = {name: hashlib.sha256((Path(args.workspace) / 'src/engine/scalping' / name).read_bytes()).hexdigest()
                   for name in ('ai_action_outcome_calibration.py', 'entry_strategy_policy.py',
                                'compact_auxiliary_paired_replay.py')}
    helper = Path(args.workspace) / 'src/engine/scalping/postclose_entry_validation.py'
    if helper.is_file():
        code_sha256[helper.name] = hashlib.sha256(helper.read_bytes()).hexdigest()
    wall, cpu = time.perf_counter(), time.process_time()
    if args.family == 'machine':
        result = calibration.build_main_strategy_refinement(sample['machine_rows'],
            parent=sample['machine_parent'], scope=('KRX','KRX_REGULAR'),
            source_contract=sample['source_contract'], machine_policy_only=True, limit=96)
        details = {'candidate_count': result['evaluated_candidate_count'],
                   'input_count': result['population_count'],
                   'selection_version': result.get('selection_basis'),
                   'candidate_sha256': result.get('machine_policy_sha256'),
                   'promotion_pass': result['promotion_pass'],
                   'promotion_errors': result.get('promotion_errors'),
                   'economics': ((result.get('machine_evidence') or {}).get('train') or {}).get('economics'),
                   'cache_receipts': [s.get('replay_coverage') for s in result.get('machine_candidate_scores') or []]}
    else:
        result = compact.evaluate_auxiliary_stage(sample['auxiliary_projection'], sample['prompt_results'])
        details = {'eligible_count': result['eligible_count'],
                   'scopes': {scope: {'status': value['status'],
                      'candidate_count': len(value['candidates']),
                      'selection_version': value['selection_rank_version'],
                      'frozen_train_choice': value.get('frozen_train_choice'),
                      'holdout_errors': value.get('holdout_errors')}
                      for scope,value in result['scope_results'].items()}}
    sys.stdout = output
    print(json.dumps({'family': args.family, 'version': args.version,
        'wall_sec': time.perf_counter()-wall, 'cpu_sec': time.process_time()-cpu,
        'peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'input_sha256': compact.digest(sample), 'provider_calls': 0,
        'code_sha256': code_sha256,
        'policy_written': False, 'historical_regression_not_forward_acceptance': True,
        'details': details}, ensure_ascii=False))


if __name__ == '__main__':
    main()
