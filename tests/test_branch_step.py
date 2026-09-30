"""branch-step: git next / keep / drop と pre-push hook を一時 repo で検証する。
Run with python3 -m unittest discover -s tests -v. gh は呼ばない（--dry-run）。"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/branch-step/scripts/branch-step"
HOOK = ROOT / "skills/branch-step/hooks/pre-push"


class BranchStepTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.env = {
            **os.environ,
            "HOME": str(base / "home"),
            "GIT_CONFIG_GLOBAL": str(base / "home/.gitconfig"),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com",
            "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.com",
        }
        (base / "home").mkdir()
        self.origin = base / "origin.git"
        self.git("init", "--bare", "-q", str(self.origin), cwd=base)
        self.work = base / "work"
        self.git("clone", "-q", str(self.origin), str(self.work), cwd=base)
        self.git("checkout", "-q", "-b", "main")
        self.commit("init")
        self.git("push", "-q", "-u", "origin", "main")
        self.git("checkout", "-q", "-b", "nightly")
        self.git("push", "-q", "-u", "origin", "nightly")

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args, cwd=None, check=True):
        return subprocess.run(["git", *args], cwd=cwd or self.work, env=self.env,
                              text=True, capture_output=True, check=check)

    def commit(self, name, path=None):
        target = self.work / (path or f"{name}.txt")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(name + "\n")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", name)

    def step(self, *args, check=True):
        return subprocess.run(["bash", str(SCRIPT), *args], cwd=self.work, env=self.env,
                              text=True, capture_output=True, check=check)

    def branch(self):
        return self.git("branch", "--show-current").stdout.strip()

    def local_branches(self):
        return set(self.git("for-each-ref", "--format=%(refname:short)", "refs/heads").stdout.split())

    def remote_branches(self):
        out = self.git("ls-remote", "--heads", "origin").stdout
        return {line.split("refs/heads/")[1] for line in out.splitlines()}

    def test_scripts_parse(self):
        for path, shell in ((SCRIPT, "bash"), (HOOK, "sh")):
            subprocess.run([shell, "-n", str(path)], check=True)
        self.assertTrue(os.access(SCRIPT, os.X_OK) and os.access(HOOK, os.X_OK))

    def test_push_failure_leaves_wip_untouched(self):
        self.git("checkout", "-q", "-b", "wip/x")
        self.commit("a")
        self.git("remote", "set-url", "origin", str(Path(self.tmp.name) / "missing.git"))
        result = self.step("next", "--memory", "mem_T", "--dry-run", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.branch(), "wip/x", "push に失敗したら rename しない")

    # --- next ---

    def test_next_promotes_spike_to_wip_and_head_follows(self):
        self.git("checkout", "-q", "-b", "spike/x")
        self.commit("a")
        self.step("next")
        self.assertEqual(self.branch(), "wip/x")
        self.assertNotIn("spike/x", self.local_branches())

    def test_next_promotes_exp_to_wip_and_removes_remote_exp(self):
        self.git("checkout", "-q", "-b", "exp/x")
        self.commit("a")
        self.git("push", "-q", "-u", "origin", "exp/x")
        self.step("next")
        self.assertEqual(self.branch(), "wip/x")
        self.assertNotIn("exp/x", self.remote_branches())

    def test_next_wip_to_review_pushes_and_prints_pr_command(self):
        self.git("checkout", "-q", "-b", "wip/x")
        self.commit("a")
        self.git("push", "-q", "-u", "origin", "wip/x")
        result = self.step("next", "--memory", "mem_TEST123", "--dry-run")
        self.assertEqual(self.branch(), "review/x")
        self.assertIn("review/x", self.remote_branches())
        self.assertNotIn("wip/x", self.remote_branches(), "wip の backup push は消す")
        self.assertIn("gh pr create", result.stdout)
        self.assertIn("--base nightly", result.stdout)
        self.assertIn("--head review/x", result.stdout)
        self.assertIn("mem_TEST123", result.stdout)

    def test_next_uses_main_when_nightly_is_absent(self):
        self.git("checkout", "-q", "main")
        self.git("branch", "-q", "-D", "nightly")
        self.git("push", "-q", "origin", "--delete", "nightly")
        self.git("checkout", "-q", "-b", "wip/x")
        self.commit("a")
        result = self.step("next", "--memory", "mem_T", "--dry-run")
        self.assertIn("--base main", result.stdout)

    def test_next_to_review_requires_memory_unless_no_pr(self):
        self.git("checkout", "-q", "-b", "wip/x")
        self.commit("a")
        result = self.step("next", "--dry-run", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.branch(), "wip/x", "門で止まったら rename しない")
        self.assertNotIn("review/x", self.remote_branches())
        self.step("next", "--no-pr")
        self.assertEqual(self.branch(), "review/x")
        self.assertIn("review/x", self.remote_branches())

    def test_next_refuses_review_and_hotfix(self):
        for name in ("review/x", "hotfix/y"):
            self.git("checkout", "-q", "-b", name)
            self.commit(name.replace("/", "-"))
            result = self.step("next", check=False)
            self.assertNotEqual(result.returncode, 0, name)
            self.assertEqual(self.branch(), name)

    def test_next_gate_runs_configured_test_command(self):
        self.git("checkout", "-q", "-b", "wip/x")
        self.commit("a")
        self.git("config", "branch-step.test", "false")
        result = self.step("next", "--memory", "mem_T", "--dry-run", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.branch(), "wip/x")
        self.git("config", "branch-step.test", "true")
        self.step("next", "--memory", "mem_T", "--dry-run")
        self.assertEqual(self.branch(), "review/x")

    def test_next_gate_warns_when_code_changed_without_design(self):
        (self.work / "docs/design").mkdir(parents=True)
        self.commit("design", "docs/design/01-a.md")
        self.git("push", "-q", "origin", "nightly")
        self.git("checkout", "-q", "-b", "wip/x")
        self.commit("code", "src/a.rs")
        result = self.step("next", "--memory", "mem_T", "--dry-run")
        self.assertIn("design", result.stderr)
        self.assertEqual(self.branch(), "review/x", "警告だけで止めない")
        self.git("checkout", "-q", "-b", "wip/y", "nightly")
        self.commit("code2", "src/b.rs")
        self.commit("design2", "docs/design/02-b.md")
        result = self.step("next", "--memory", "mem_T", "--dry-run")
        self.assertNotIn("design", result.stderr)

    # --- slug の解決 ---

    def test_slug_argument_finds_branch_from_elsewhere(self):
        self.git("checkout", "-q", "-b", "spike/x")
        self.commit("a")
        self.git("checkout", "-q", "nightly")
        self.step("next", "x")
        self.assertIn("wip/x", self.local_branches())
        self.assertEqual(self.branch(), "nightly")

    def test_ambiguous_or_missing_slug_fails(self):
        self.git("branch", "-q", "spike/x")
        self.git("branch", "-q", "wip/x")
        self.assertNotEqual(self.step("next", "x", check=False).returncode, 0)
        self.assertNotEqual(self.step("next", "nope", check=False).returncode, 0)
        self.assertNotEqual(self.step("next", check=False).returncode, 0, "trunk 上で slug 無しは失敗")

    # --- keep / drop ---

    def test_keep_moves_spike_to_exp_and_pushes(self):
        self.git("checkout", "-q", "-b", "spike/x")
        self.commit("a")
        self.step("keep")
        self.assertEqual(self.branch(), "exp/x")
        self.assertIn("exp/x", self.remote_branches())
        self.assertNotEqual(self.step("keep", check=False).returncode, 0, "keep は spike だけ")

    def test_drop_deletes_spike_only(self):
        self.git("checkout", "-q", "-b", "spike/x")
        self.commit("a")
        self.step("drop")
        self.assertNotIn("spike/x", self.local_branches())
        self.assertEqual(self.branch(), "nightly")
        self.git("checkout", "-q", "-b", "wip/y")
        self.commit("b")
        self.assertNotEqual(self.step("drop", check=False).returncode, 0)
        self.assertIn("wip/y", self.local_branches())

    # --- install と pre-push hook ---

    def test_install_sets_aliases_and_hook(self):
        self.step("install")
        self.assertIn("next", self.git("config", "--get", "alias.next").stdout)
        hook = self.work / ".git/hooks/pre-push"
        self.assertTrue(os.access(hook, os.X_OK))
        self.git("checkout", "-q", "-b", "spike/x")
        self.commit("a")
        self.git("next")
        self.assertEqual(self.branch(), "wip/x")

    def test_install_does_not_overwrite_foreign_hook(self):
        hook = self.work / ".git/hooks/pre-push"
        hook.write_text("#!/bin/sh\nexit 0\n")
        result = self.step("install", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(hook.read_text(), "#!/bin/sh\nexit 0\n")

    def test_pre_push_rejects_spike_and_allows_others(self):
        self.step("install")
        self.git("checkout", "-q", "-b", "spike/x")
        self.commit("a")
        result = self.git("push", "origin", "spike/x", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("spike", result.stderr)
        self.assertNotIn("spike/x", self.remote_branches())
        result = self.git("push", "origin", "spike/x:refs/heads/wip/x", check=False)
        self.assertNotEqual(result.returncode, 0, "spike を別名で押すのも拒否")
        self.git("checkout", "-q", "-b", "wip/y")
        self.git("push", "-q", "origin", "wip/y")
        self.assertIn("wip/y", self.remote_branches())

    def test_pre_push_allows_deleting_remote_spike(self):
        self.git("checkout", "-q", "-b", "spike/x")
        self.commit("a")
        self.git("push", "-q", "origin", "spike/x")
        self.step("install")
        self.git("push", "-q", "origin", "--delete", "spike/x")
        self.assertNotIn("spike/x", self.remote_branches())

    def test_board_lists_step_refs(self):
        self.git("branch", "-q", "spike/a")
        self.git("branch", "-q", "wip/b")
        out = self.step("board").stdout
        self.assertIn("spike/a", out)
        self.assertIn("wip/b", out)


if __name__ == "__main__":
    unittest.main()
