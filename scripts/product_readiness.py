"""Evidence completeness, never a claim of certification or source verification."""
import csv
import json
import math
from pathlib import Path
from rag_service import utc

ROOT = Path(__file__).resolve().parents[1]


def read_csv(name):
    with (ROOT / 'evidence' / name).open() as f: return list(csv.DictReader(f))


def readiness():
    ledger = read_csv('pain-ledger.csv')
    records = [r for r in ledger if r.get('origin') == 'real' and all(r.get(k, '').strip() for k in ('verbatim', 'source_reference', 'permission_scope', 'verified_by'))]
    people = {r['participant_code'] for r in records if r.get('outside_team', '').lower() == 'true' and r.get('participant_code') and r.get('source_type') in ('interview', 'survey')}
    mined = [r for r in records if r.get('source_type') == 'mining']
    impacts = []
    for r in read_csv('impact-candidates.csv'):
        try:
            values = [float(r[k]) for k in ('people_count', 'frequency_per_month', 'minutes_per_occurrence')]
            if any(not math.isfinite(v) or v <= 0 for v in values) or not r.get('basis_source'): continue
            impacts.append({'id': r['candidate_id'], 'decision': r['decision'], 'hours_per_month': round(values[0] * values[1] * values[2] / 60, 2), 'basis_source': r['basis_source'], 'verified': False})
        except (ValueError, KeyError): continue
    eval_file = ROOT / 'evaluations/reports/grounding.json'
    evaluation = json.loads(eval_file.read_text()) if eval_file.exists() else {}
    benchmarks = [r for r in read_csv('benchmarks.csv') if r.get('origin') == 'real' and r.get('reviewer')]
    return {'generated_at': utc(), 'status': 'not_ready_for_rubric_claim', 'notice': 'Kiểm tra độ đầy đủ hồ sơ, không xác minh tính đúng của nguồn hoặc chứng nhận Level 3.', 'prototype': {'status': 'implemented', 'mode': 'local_extractive_baseline', 'llm': False}, 'pain_evidence': {'status': 'recorded_requires_review' if len(people) >= 20 else 'mining_requires_manual_review' if mined else 'missing', 'outside_team_participants': len(people), 'traceable_real_records': len(records)}, 'impact': {'status': 'recorded_requires_review' if any(r['decision'] == 'selected' for r in impacts) and any(r['decision'] == 'rejected' for r in impacts) else 'missing', 'candidates': impacts}, 'evaluation': {'synthetic_cases': evaluation.get('total_cases', 0), 'system_passed': evaluation.get('passed_cases', 0), 'real_cases': evaluation.get('real_cases', 0), 'model_status': evaluation.get('model_evaluation', {}).get('status', 'not_run')}, 'value_measurement': {'status': 'recorded_requires_review' if benchmarks else 'missing', 'real_runs': len(benchmarks)}}


if __name__ == '__main__':
    result = readiness();folder = ROOT / 'evaluations/reports';folder.mkdir(parents=True, exist_ok=True)
    (folder / 'readiness.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps(result, ensure_ascii=False, indent=2))
