"""Run with python3 -m unittest discover -s tests -v. No external services.

hooks は Ruby（system ruby 2.6 でも動く書き方）。振る舞いは fail-open、報告は黙らない:
- session-start: 常に exit 0 + JSON。出せる context は出し、失敗は systemMessage で知らせる
- fabrication-tripwire: 判定できないときは block せず、exit 1 + stderr 一行で知らせる

別の ruby で確かめるときは HOOKS_RUBY=/usr/bin/ruby を付ける。
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
RUBY = shutil.which(os.environ.get("HOOKS_RUBY", "ruby")) or "ruby"


def claude(role, content):
    return {"type": role, "message": {"content": content}}


def codex(kind, **fields):
    return {"type": "response_item", "payload": {"type": kind, **fields}}


class HooksTest(unittest.TestCase):
    def run_raw(self, name, stdin, **kwargs):
        return subprocess.run(
            [RUBY, str(ROOT / "hooks" / name)],
            input=stdin, text=True, capture_output=True, timeout=10, **kwargs,
        )

    def run_hook(self, name, payload, **kwargs):
        result = self.run_raw(name, json.dumps(payload), **kwargs)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout) if result.stdout.strip() else {}

    def assert_skipped_loudly(self, result):
        # block しない（stdout 無し）が、黙らない（exit 1、stderr の先頭行は hook 名から）
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(result.stdout.strip(), "")
        self.assertTrue(result.stderr.startswith("chronista-style fabrication-tripwire:"), result.stderr)

    def write_transcript(self, directory, records):
        path = Path(directory) / "transcript.jsonl"
        path.write_text("\n".join(json.dumps(r) for r in records) + "\n")
        return str(path)

    def stop(self, records, **fields):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_transcript(directory, records)
            return self.run_hook("fabrication_tripwire.rb", {"transcript_path": path, **fields})

    def stop_raw(self, records, **fields):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_transcript(directory, records)
            return self.run_raw("fabrication_tripwire.rb", json.dumps({"transcript_path": path, **fields}))

    def transcripts(self, evidence=None, final="test result: ok", kind="custom_tool_call_output"):
        c = [claude("user", "test please")]
        x = [codex("message", role="user", content=[{"type": "input_text", "text": "test please"}])]
        if evidence is not None:
            c.append(claude("user", [{"type": "tool_result", "content": evidence}]))
            x.append(codex(kind, call_id="call1", output=evidence))
        c.append(claude("assistant", [{"type": "text", "text": final}]))
        x.append(codex("message", role="assistant", phase="final_answer",
                       content=[{"type": "output_text", "text": final}]))
        return c, x

    def test_unbacked_report_blocks_both_formats(self):
        for records in self.transcripts():
            with self.subTest(records=records):
                self.assertEqual(self.stop(records).get("decision"), "block")

    def test_real_results_support_report(self):
        for kind in ("custom_tool_call_output", "function_call_output"):
            for evidence in ("test result: ok", [{"type": "text", "text": "test result: ok"}],
                             [{"type": "input_text", "text": "test result: ok"}]):
                for records in self.transcripts(evidence, kind=kind):
                    self.assertNotEqual(self.stop(records).get("decision"), "block")

    def test_previous_turn_evidence_supports_recap(self):
        for records in self.transcripts("test result: ok"):
            records += self.transcripts(final="test result: ok")[0 if records[0]["type"] == "user" else 1]
            self.assertNotEqual(self.stop(records).get("decision"), "block")

    def test_user_and_tool_call_text_are_not_evidence(self):
        records = [codex("message", role="user", content=[{"type": "input_text", "text": "test result: ok"}]),
                   codex("custom_tool_call", name="exec", input="test result: ok")]
        records += self.transcripts()[1][-1:]
        self.assertEqual(self.stop(records).get("decision"), "block")

    def test_hook_final_text_takes_priority(self):
        for records in self.transcripts():
            self.assertNotEqual(self.stop(records, last_assistant_message="未検証です").get("decision"), "block")
            self.assertNotEqual(self.stop(records, last_assistant_message="").get("decision"), "block")

    def test_commentary_is_not_final(self):
        records = self.transcripts()[1]
        records[-1]["payload"]["phase"] = "commentary"
        self.assertNotEqual(self.stop(records).get("decision"), "block")

    def test_new_prompt_does_not_recheck_old_final(self):
        for records in self.transcripts():
            if records[0]["type"] == "user":
                records.append(claude("user", [{"type": "text", "text": "next task"}]))
            else:
                records.append(codex("message", role="user", content=[{"type": "input_text", "text": "next task"}]))
            self.assertNotEqual(self.stop(records).get("decision"), "block")

    def test_explicit_override_only(self):
        for records in self.transcripts(final="test result: ok\nTRIPWIRE-ACK"):
            self.assertNotEqual(self.stop(records).get("decision"), "block")
        for records in self.transcripts(final="test result: ok (TRIPWIRE-ACK)"):
            self.assertEqual(self.stop(records).get("decision"), "block")

    def test_continuation_does_not_loop(self):
        for records in self.transcripts():
            self.assertNotEqual(self.stop(records, stop_hook_active=True).get("decision"), "block")

    def test_unknown_and_broken_transcripts_skip_loudly(self):
        # 判定できないときは block しない。ただし黙らない
        self.assert_skipped_loudly(self.stop_raw([{"type": "future_format", "output": "unknown"}],
                                                 last_assistant_message="test result: ok"))
        self.assert_skipped_loudly(self.run_raw("fabrication_tripwire.rb", json.dumps({"transcript_path": "/missing"})))
        self.assert_skipped_loudly(self.run_raw("fabrication_tripwire.rb", json.dumps({})))
        self.assert_skipped_loudly(self.run_raw("fabrication_tripwire.rb", "{broken"))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "broken.jsonl"
            path.write_text(json.dumps(self.transcripts()[1][0]) + "\n{broken")
            self.assert_skipped_loudly(self.run_raw("fabrication_tripwire.rb", json.dumps({
                "transcript_path": str(path), "last_assistant_message": "test result: ok",
            })))

    def test_unknown_output_shape_is_not_missing_evidence(self):
        records = self.transcripts()[1]
        records.insert(1, codex("custom_tool_call_output", output=[{"type": "future_text", "value": "test result: ok"}]))
        self.assert_skipped_loudly(self.stop_raw(records))

    def test_claude_feedback_and_final_rewrite(self):
        records = self.transcripts("test result: ok")[0]
        records += [claude("user", "Stop hook feedback: retry"),
                    claude("assistant", [{"type": "text", "text": "test result: ok"}])]
        self.assertEqual(self.stop(records), {})

    def test_session_legacy_environment_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            env = dict(os.environ, CLAUDE_PROJECT_DIR=directory)
            result = self.run_hook("session_start.rb", {}, env=env)
            self.assertIn(Path(directory).name, result["hookSpecificOutput"]["additionalContext"])

    def test_session_git_context_comes_from_requested_repo(self):
        with tempfile.TemporaryDirectory() as directory:
            subprocess.run(["git", "init", "-q", directory], check=True)
            subprocess.run(["git", "-C", directory, "symbolic-ref", "HEAD", "refs/heads/hook-test"], check=True)
            subprocess.run(["git", "-C", directory, "remote", "add", "origin", "git@example.test:org/plugin-atlas.git"], check=True)
            result = self.run_hook("session_start.rb", {"cwd": directory}, cwd=ROOT)
            context = result["hookSpecificOutput"]["additionalContext"]
            self.assertIn("hook-test", context)
            self.assertIn("remote 由来: `atlas`", context)
            self.assertNotIn("systemMessage", result)

    def test_session_cwd_precedes_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / 'codex-plugin-project "日本語"'
            project.mkdir()
            env = dict(os.environ, CLAUDE_PROJECT_DIR=str(ROOT))
            result = self.run_hook("session_start.rb", {"cwd": str(project)}, env=env, cwd=ROOT)
            context = result["hookSpecificOutput"]["additionalContext"]
            self.assertIn(project.name, context)
            self.assertIn('project "日本語"', context)
            # git リポジトリでないのは異常ではない。警告を出さない
            self.assertIn("Branch: `-`", context)
            self.assertNotIn("systemMessage", result)

    def test_session_invalid_cwd_warns_and_never_reports_other_repo(self):
        result = self.run_hook("session_start.rb", {"cwd": "/missing/chronista-project"}, cwd=ROOT)
        self.assertNotIn("hookSpecificOutput", result)
        self.assertTrue(result["systemMessage"].startswith("chronista-style session-start:"), result)
        self.assertIn("/missing/chronista-project", result["systemMessage"])

    def test_session_broken_stdin_warns_but_still_injects(self):
        with tempfile.TemporaryDirectory() as directory:
            env = dict(os.environ, CLAUDE_PROJECT_DIR=directory)
            result = self.run_raw("session_start.rb", "{broken", env=env)
            self.assertEqual(result.returncode, 0, result.stderr)
            out = json.loads(result.stdout)
            self.assertIn(Path(directory).name, out["hookSpecificOutput"]["additionalContext"])
            self.assertTrue(out["systemMessage"].startswith("chronista-style session-start:"), out)

    def test_session_missing_git_warns_but_still_injects(self):
        # PATH から git を消す。ruby は絶対パスで起動しているが、macOS の system ruby は起動時に uname を呼ぶので残す
        with tempfile.TemporaryDirectory() as directory:
            bin_dir = Path(directory) / "bin"
            bin_dir.mkdir()
            uname = shutil.which("uname")
            if uname:
                (bin_dir / "uname").symlink_to(uname)
            env = dict(os.environ, PATH=str(bin_dir))
            result = self.run_raw("session_start.rb", json.dumps({"cwd": directory}), env=env)
            self.assertEqual(result.returncode, 0, result.stderr)
            out = json.loads(result.stdout)
            self.assertIn(Path(directory).name, out["hookSpecificOutput"]["additionalContext"])
            self.assertIn("git", out["systemMessage"])


if __name__ == "__main__":
    unittest.main()
