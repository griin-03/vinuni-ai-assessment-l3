"""Check tracked/staged repository content without displaying secret values.

This is a narrow local guard, not a replacement for GitHub secret scanning.
Run after git add so the exact index that will be committed is inspected.
"""
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SECRET_PATTERNS = {
    'github_token': re.compile(rb'gh[pousr]_[A-Za-z0-9]{20,}'),
    'github_fine_grained_token': re.compile(rb'github_pat_[A-Za-z0-9_]{30,}'),
    'private_key': re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'),
    'aws_access_key': re.compile(rb'(?:AKIA|ASIA)[A-Z0-9]{16}'),
    'discord_webhook': re.compile(rb'https://(?:canary\.|ptb\.)?discord(?:app)?\.com/api/webhooks/[0-9]+/[A-Za-z0-9_-]{20,}'),
    'discord_bot_token': re.compile(rb'(?<![A-Za-z0-9_-])[A-Za-z0-9_-]{23,28}\.[A-Za-z0-9_-]{6}\.[A-Za-z0-9_-]{27,40}(?![A-Za-z0-9_-])'),
}
DATABASE_URL = re.compile(rb'(?:mysql|postgres(?:ql)?)://[^\s/<>:@]+:([^@\s<>]+)@[^\s<>]+')
PLACEHOLDERS = {b'PASSWORD', b'password', b'REPLACE_ME', b'YOUR_PASSWORD', b'PLACEHOLDER'}
FORBIDDEN_ROOTS = {'.vinassess', 'node_modules', 'backups', 'reference', 'cdn-cgi'}


def index_files():
    raw = subprocess.check_output(['git', 'ls-files', '--stage', '-z'], cwd=ROOT)
    files = []
    for record in raw.split(b'\0'):
        if not record: continue
        metadata, path = record.split(b'\t', 1)
        mode, sha, stage = metadata.split()
        if stage != b'0': raise RuntimeError('Resolve merge conflicts before checking the index.')
        files.append((path.decode('utf-8'), sha.decode(), mode.decode()))
    if not files: raise RuntimeError('No tracked files. Stage the intended files with git add first.')
    batch = subprocess.run(['git', 'cat-file', '--batch'], input=('\n'.join(sha for _, sha, _ in files) + '\n').encode(), stdout=subprocess.PIPE, check=True, cwd=ROOT).stdout
    position = 0
    result = []
    for path, _, mode in files:
        end = batch.index(b'\n', position)
        header = batch[position:end].split()
        size = int(header[2]); position = end + 1
        result.append((path, batch[position:position + size], mode))
        position += size + 1
    return result


def check(files):
    issues = []
    names = {path for path, _, _ in files}
    for path, data, mode in files:
        parts = Path(path).parts
        if parts[0] in FORBIDDEN_ROOTS or any(p in ('__pycache__', '.venv', 'venv') for p in parts):
            issues.append({'path': path, 'rule': 'private_or_generated_directory'})
        if any(p.startswith('.env') and p != '.env.example' for p in parts) or Path(path).suffix.lower() in ('.pem', '.key', '.p12', '.pfx', '.sqlite', '.sqlite3', '.db'):
            issues.append({'path': path, 'rule': 'private_configuration_or_database'})
        if mode == '120000': issues.append({'path': path, 'rule': 'review_symlink_before_distribution'})
        if len(data) > 10 * 1024 * 1024: issues.append({'path': path, 'rule': 'file_exceeds_10_mib'})
        if b'\x00' in data[:4096]: continue
        for rule, pattern in SECRET_PATTERNS.items():
            for match in pattern.finditer(data):
                issues.append({'path': path, 'line': data[:match.start()].count(b'\n') + 1, 'rule': rule})
        for match in DATABASE_URL.finditer(data):
            if match[1] not in PLACEHOLDERS:
                issues.append({'path': path, 'line': data[:match.start()].count(b'\n') + 1, 'rule': 'database_url_with_password'})
    manifest = json.loads(dict((path, data) for path, data, _ in files)['content/landing-assets.json'])
    for asset in manifest['assets'].values():
        if asset['path'] not in names:
            issues.append({'path': asset['path'], 'rule': 'runtime_asset_missing_from_git'})
    for required in ['README.md', 'CONTRIBUTING.md', '.env.example', 'vendor/landing-baseline/index.html', 'docs/team/README.md', 'docs/team/six-week-plan.md']:
        if required not in names: issues.append({'path': required, 'rule': 'required_team_file_missing'})
    return issues


if __name__ == '__main__':
    try:
        files = index_files(); issues = check(files)
        print(json.dumps({'checked_index_files': len(files), 'issues': issues, 'passed': not issues}, ensure_ascii=False, indent=2))
        sys.exit(bool(issues))
    except (subprocess.CalledProcessError, RuntimeError, KeyError, ValueError) as error:
        print('Repository check could not finish: ' + type(error).__name__ + '. Check index and manifest; no secret values are printed.', file=sys.stderr)
        sys.exit(2)
