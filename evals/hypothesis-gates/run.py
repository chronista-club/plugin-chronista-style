#!/usr/bin/env python3
"""Run one host/version against fixed anonymous fixtures; never loads private logs."""
import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path
import subprocess
import time
import uuid

HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--host', choices=['claude', 'codex'], required=True)
parser.add_argument('--skills', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--case')
parser.add_argument('--model', required=True)
parser.add_argument('--effort', default='high')
args = parser.parse_args()
args.skills = args.skills.resolve()
args.output = args.output.resolve()
args.output.mkdir(parents=True, exist_ok=True)
cases = json.loads((HERE/'cases.json').read_text())
for case in cases:
    if args.case and case['id'] != args.case:
        continue
    run_id = uuid.uuid4().hex[:12]
    run = args.output/run_id
    workspace = run/'workspace'
    workspace.mkdir(parents=True)
    for name, body in case['files'].items():
        target = workspace/name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body)
    env = {k:v for k,v in os.environ.items() if not k.startswith('GIT_') and k not in ['CLAUDECODE']}
    subprocess.run(['git','init','-q'],cwd=workspace,env=env,check=True)
    subprocess.run(['git','add','.'],cwd=workspace,env=env,check=True)
    for name in case['skills']:
        shutil.copytree(args.skills/name, workspace/'evaluation-skills'/name)
    skill_texts = {name:(args.skills/name/'SKILL.md').read_text() for name in case['skills']}
    prompt = ('隔離した評価用ワークスペースで次の依頼を実行してください。利用可能なスキル本文を以下に添付します。'
              'このディレクトリ内の合成fixtureだけを扱い、外部サービス・ユーザー設定・他のrepoには触れないでください。'
              '配布、commit、push、別エージェント起動は不要です。実行と変更はこのワークスペース内で行ってください。'
              'この実行環境ではBashのシェル制御構文（cd、for、パイプ等）は許可されません。Read/Write/Editと /usr/bin/python3 の単独コマンドを使ってください。Python内の一時ディレクトリ操作とsubprocess呼出しは可能です。Pythonには /usr/bin/python3 を使ってください。記憶サービスは未接続です。日本語で簡潔に報告してください。\n\n'
              + '\n\n'.join(f'<skill name="{name}" source="evaluation-skills/{name}/SKILL.md">\n{body}\n</skill>' for name,body in skill_texts.items())
              + '\n\n依頼:\n'+case['request'])
    (run/'prompt.txt').write_text(prompt)
    env = {k:v for k,v in os.environ.items() if not k.startswith('GIT_') and k not in ['CLAUDECODE']}
    if args.host == 'claude':
        command = ['claude','--model',args.model,'--setting-sources','','--safe-mode','--print','--no-session-persistence','--output-format','stream-json',
                   '--verbose','--permission-mode','dontAsk','--tools','Bash,Read,Edit,Write',
                   '--allowedTools','Bash(/usr/bin/python3 *),Bash(python3 *),Bash(git *),Bash(cat *),Bash(ls*),Bash(rg *),Bash(pwd*),Bash(echo *),Bash(env *),Bash(FAULT=*),Bash(for *),Bash(sed *),Bash(head *),Bash(wc *),Read,Edit,Write']
    else:
        # Keep auth at its existing location without reading or copying credentials.
        codex_dir = run/'codex-home'
        codex_dir.mkdir()
        (codex_dir/'auth.json').symlink_to(Path.home()/'.codex/auth.json')
        env['CODEX_HOME'] = str(codex_dir)
        command = ['codex','exec','--ignore-user-config','--ignore-rules','--ephemeral','--json',
                   '--sandbox','workspace-write','-c','approval_policy="never"',
                   '-c',f'model={json.dumps(args.model)}','-c',f'model_reasoning_effort={json.dumps(args.effort)}',
                   '-o',str(run/'final.txt'),'-']
    started = time.monotonic()
    with (run/'events.jsonl').open('w') as stdout, (run/'stderr.txt').open('w') as stderr:
        try:
            result = subprocess.run(command,input=prompt,text=True,cwd=workspace,env=env,
                                    stdout=stdout,stderr=stderr,timeout=240)
            returncode = result.returncode
        except subprocess.TimeoutExpired:
            returncode = 'timeout'
    if args.host == 'codex':
        (codex_dir/'auth.json').unlink()
    diff = subprocess.run(['git','diff','--no-ext-diff'],cwd=workspace,env=env,capture_output=True,text=True,check=True).stdout
    (run/'diff.patch').write_text(diff)
    # Include newly created tests as artifacts, not just the tracked-file diff.
    artifacts = {str(p.relative_to(workspace)):p.read_text(errors='replace') for p in workspace.rglob('*')
                 if p.is_file() and '.git' not in p.parts and '__pycache__' not in p.parts and 'evaluation-skills' not in p.parts}
    (run/'artifacts.json').write_text(json.dumps(artifacts,ensure_ascii=False,indent=2))
    metadata = {'run_id':run_id,'host':args.host,'case':case['id'],'returncode':returncode,
                'seconds':round(time.monotonic()-started,2),'command':command,'model':args.model,'effort':args.effort if args.host == 'codex' else 'host-default',
                'skill_sha256':{n:hashlib.sha256(t.encode()).hexdigest() for n,t in skill_texts.items()}}
    (run/'metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:metadata[k] for k in ['run_id','host','case','returncode','seconds']}),flush=True)
    if returncode != 0:
        print('Host invocation failed; stop this batch rather than count it as skill behavior.',flush=True)
        break
