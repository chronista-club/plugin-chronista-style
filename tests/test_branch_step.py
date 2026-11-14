"""branch-step: git next / keep / drop と pre-push hook を一時 repo で検証する。
Run with python3 -m unittest discover -s tests -v. gh は呼ばない（--print-pr）。"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/branch-step/scripts/branch-step"
HOOK = ROOT / "skills/branch-step/hooks/pre-push"
BIN = ROOT / "bin"


class BranchStepTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.env = {
            **{k: v for k, v in os.environ.items() if not k.startswith("GIT_")},
            "HOME": str(base / "home"),
            "GIT_CONFIG_GLOBAL": str(base / "home/.gitconfig"),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com",
            "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.com",
        }
        # plugin の bin/（git-next 等）が PATH に入った session から走っても同じ結果にする。
        # git は PATH 上の git-<name> を alias より先に動かすので、残すと alias を見る test が別の実体を呼ぶ。
        # bin/ 経由の振る舞いは git_bin() が明示して見る
        self.env["PATH"] = os.pathsep.join(
            d for d in self.env.get("PATH", "").split(os.pathsep)
            if d and not (Path(d) / "git-next").exists())
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
        self.git("config", "branch-step.enabled", "true")

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args, cwd=None, check=True):
        return subprocess.run(["git", *args], cwd=cwd or self.work, env=self.env,
                              text=True, capture_output=True, check=check)

    def git_bin(self, *args, cwd=None, check=True):
        """plugin の bin/ を PATH の先頭に入れた git。Claude Code が有効な plugin の bin/ を PATH に足すのと同じ形。"""
        env = {**self.env, "PATH": f"{BIN}{os.pathsep}{self.env['PATH']}"}
        return subprocess.run(["git", *args], cwd=cwd or self.work, env=env,
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

    def fake_gh(self, create_exit=0, view_exit=1):
        """auth status は成功、pr create / pr view の exit を指定できる偽 gh を PATH 先頭に置く。"""
        bindir = Path(self.tmp.name) / "fakebin"
        bindir.mkdir(exist_ok=True)
        gh = bindir / "gh"
        gh.write_text(f"""#!/bin/sh
case "$1 $2" in
  "auth status") exit 0 ;;
  "pr create") echo "fake-pr-created $*"; exit {create_exit} ;;
  "pr view") exit {view_exit} ;;
esac
exit 1
""")
        gh.chmod(0o755)
        return {**self.env, "PATH": f"{bindir}:{self.env['PATH']}"}

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
        result = self.step("next", "--memory", "mem_T", "--print-pr", check=False)
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
        result = self.step("next", "--memory", "mem_TEST123", "--print-pr")
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
        result = self.step("next", "--memory", "mem_T", "--print-pr")
        self.assertIn("--base main", result.stdout)

    def test_next_to_review_requires_memory_unless_no_pr(self):
        self.git("checkout", "-q", "-b", "wip/x")
        self.commit("a")
        result = self.step("next", "--print-pr", check=False)
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
        result = self.step("next", "--memory", "mem_T", "--print-pr", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.branch(), "wip/x")
        self.git("config", "branch-step.test", "true")
        self.step("next", "--memory", "mem_T", "--print-pr")
        self.assertEqual(self.branch(), "review/x")

    def test_next_gate_warns_when_code_changed_without_design(self):
        (self.work / "docs/design").mkdir(parents=True)
        self.commit("design", "docs/design/01-a.md")
        self.git("push", "-q", "origin", "nightly")
        self.git("checkout", "-q", "-b", "wip/x")
        self.commit("code", "src/a.rs")
        result = self.step("next", "--memory", "mem_T", "--print-pr")
        self.assertIn("design", result.stderr)
        self.assertEqual(self.branch(), "review/x", "警告だけで止めない")
        self.git("checkout", "-q", "-b", "wip/y", "nightly")
        self.commit("code2", "src/b.rs")
        self.commit("design2", "docs/design/02-b.md")
        result = self.step("next", "--memory", "mem_T", "--print-pr")
        self.assertNotIn("design", result.stderr)

    def test_gate_runs_in_the_worktree_of_the_branch(self):
        self.git("checkout", "-q", "-b", "wip/g")
        self.commit("FAIL", "FAIL")
        self.git("checkout", "-q", "nightly")
        self.git("config", "branch-step.test", "test ! -e FAIL")
        result = self.step("next", "g", "--no-pr", check=False)
        self.assertNotEqual(result.returncode, 0, "どこにも checkout されていないブランチの門は走れない")
        self.assertIn("wip/g", self.local_branches())
        wt = Path(self.tmp.name) / "wt-g"
        self.git("worktree", "add", "-q", str(wt), "wip/g")
        result = self.step("next", "g", "--no-pr", check=False)
        self.assertNotEqual(result.returncode, 0, "ブランチの worktree に FAIL があるので門で止まる")
        self.assertIn("wip/g", self.local_branches())
        (wt / "FAIL").unlink()
        self.git("add", "-A", cwd=wt)
        self.git("commit", "-q", "-m", "fix", cwd=wt)
        self.step("next", "g", "--no-pr")
        self.assertEqual(self.git("branch", "--show-current", cwd=wt).stdout.strip(), "review/g")

    def test_gate_refuses_dirty_worktree(self):
        self.git("checkout", "-q", "-b", "wip/d")
        self.commit("FAIL", "FAIL")
        self.git("config", "branch-step.test", "test ! -e FAIL")
        (self.work / "FAIL").unlink()
        result = self.step("next", "--no-pr", check=False)
        self.assertNotEqual(result.returncode, 0, "未 commit の状態で門を通さない")
        self.assertIn("commit", result.stderr)
        self.assertEqual(self.branch(), "wip/d")
        self.assertNotIn("review/d", self.remote_branches())

    def test_trunk_is_nightly_when_only_remote_has_it(self):
        clone = Path(self.tmp.name) / "clone"
        self.git("clone", "-q", str(self.origin), str(clone), cwd=Path(self.tmp.name))
        self.assertNotIn("nightly", self.git("for-each-ref", "--format=%(refname:short)", "refs/heads", cwd=clone).stdout)
        self.git("config", "branch-step.enabled", "true", cwd=clone)  # 印は clone ごと（local config）
        self.git("switch", "-q", "-c", "wip/f", "origin/nightly", cwd=clone)
        (clone / "f.txt").write_text("f\n")
        self.git("add", "-A", cwd=clone)
        self.git("commit", "-q", "-m", "f", cwd=clone)
        result = subprocess.run(["bash", str(SCRIPT), "next", "--memory", "mem_T", "--print-pr"],
                                cwd=clone, env=self.env, text=True, capture_output=True, check=True)
        self.assertIn("--base nightly", result.stdout)

    def test_next_exp_to_wip_pushes_wip_and_sets_upstream(self):
        self.git("checkout", "-q", "-b", "spike/x")
        self.commit("a")
        self.step("keep")
        self.step("next")
        self.assertEqual(self.branch(), "wip/x")
        self.assertIn("wip/x", self.remote_branches())
        self.assertNotIn("exp/x", self.remote_branches())
        self.assertEqual(self.git("rev-parse", "--abbrev-ref", "@{upstream}").stdout.strip(), "origin/wip/x")

    def test_print_pr_pushes_and_renames_without_calling_gh(self):
        self.git("checkout", "-q", "-b", "wip/x")
        self.commit("a")
        result = self.step("next", "--memory", "mem_T", "--print-pr")
        self.assertIn("gh pr create", result.stdout)
        self.assertEqual(self.git("rev-parse", "--abbrev-ref", "@{upstream}").stdout.strip(), "origin/review/x")

    def test_next_to_review_checks_gh_before_pushing(self):
        self.git("checkout", "-q", "-b", "wip/x")
        self.commit("a")
        bindir = Path(self.tmp.name) / "nogh"
        bindir.mkdir()
        for tool in ("git", "bash", "sh", "awk", "grep", "wc", "dirname", "cat", "sed"):
            path = subprocess.run(["which", tool], text=True, capture_output=True, check=True).stdout.strip()
            (bindir / tool).symlink_to(path)
        env = {**self.env, "PATH": str(bindir)}
        result = subprocess.run(["bash", str(SCRIPT), "next", "--memory", "mem_T"], cwd=self.work,
                                env=env, text=True, capture_output=True, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("gh", result.stderr)
        self.assertEqual(self.branch(), "wip/x")
        self.assertNotIn("review/x", self.remote_branches(), "gh が無いなら push もしない")

    def test_pr_create_failure_prints_command_and_can_be_retried(self):
        self.git("checkout", "-q", "-b", "wip/x")
        self.commit("a")
        env = self.fake_gh(create_exit=1)
        result = subprocess.run(["bash", str(SCRIPT), "next", "--memory", "mem_T"], cwd=self.work,
                                env=env, text=True, capture_output=True, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("gh pr create", result.stderr, "手で打てるコマンドを出す")
        self.assertEqual(self.branch(), "review/x")
        env = self.fake_gh(create_exit=0, view_exit=1)
        result = subprocess.run(["bash", str(SCRIPT), "next", "--memory", "mem_T"], cwd=self.work,
                                env=env, text=True, capture_output=True, check=True)
        self.assertIn("fake-pr-created", result.stdout, "review/ で PR が無ければ PR 作成だけやり直せる")
        env = self.fake_gh(create_exit=0, view_exit=0)
        result = subprocess.run(["bash", str(SCRIPT), "next"], cwd=self.work,
                                env=env, text=True, capture_output=True, check=False)
        self.assertNotEqual(result.returncode, 0, "PR があるなら review/ は語り手が PR。rename も再作成もしない")

    def test_slug_must_match_exactly_and_reject_stack_form(self):
        self.git("branch", "-q", "spike/epic/a")
        self.git("branch", "-q", "wip/epic/api")
        self.git("branch", "-q", "wip/epic/ui")
        for slug in ("epic", "*", "epic/a", "Epic", "a b"):
            result = self.step("drop", slug, check=False)
            self.assertNotEqual(result.returncode, 0, slug)
            self.assertNotIn("複数のステージ", result.stderr, slug)
        self.assertIn("spike/epic/a", self.local_branches())
        self.git("checkout", "-q", "spike/epic/a")
        result = self.step("next", check=False)
        self.assertNotEqual(result.returncode, 0, "stack 形は未決なので今いるブランチでも拒否")

    def test_drop_refuses_dirty_worktree(self):
        self.git("checkout", "-q", "-b", "spike/x")
        self.commit("a")
        (self.work / "dirty.txt").write_text("x\n")
        result = self.step("drop", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("keep", result.stderr)
        self.assertEqual(self.branch(), "spike/x")

    def test_install_defaults_to_local_and_rejects_unknown_scope(self):
        self.git("config", "--unset", "branch-step.enabled")
        self.step("install")
        self.assertEqual(self.git("config", "--local", "--get", "branch-step.enabled").stdout.strip(), "true")
        self.assertNotEqual(self.git("config", "--global", "--get", "branch-step.enabled", check=False).returncode, 0)
        self.assertNotEqual(self.step("install", "--locl", check=False).returncode, 0)
        self.step("install", "--global")
        self.assertEqual(self.git("config", "--global", "--get", "branch-step.enabled").stdout.strip(), "true")

        self.git("checkout", "-q", "-b", "wip/y")
        self.commit("b")
        self.assertNotEqual(self.step("drop", check=False).returncode, 0)
        self.assertIn("wip/y", self.local_branches())

    # --- install と pre-push hook ---

    def test_install_marks_repo_and_sets_hook_without_alias(self):
        self.git("config", "--unset", "branch-step.enabled")
        self.step("install")
        self.assertEqual(self.git("config", "--get", "branch-step.enabled").stdout.strip(), "true")
        self.assertNotEqual(self.git("config", "--get", "alias.next", check=False).returncode, 0,
                            "alias は書かない（バージョン入りの絶対パスを repo に残さない）")
        hook = self.work / ".git/hooks/pre-push"
        self.assertTrue(os.access(hook, os.X_OK))
        self.git("checkout", "-q", "-b", "spike/x")
        self.commit("a")
        self.git_bin("next")
        self.assertEqual(self.branch(), "wip/x")

    def test_install_alias_flag_writes_aliases_for_environments_without_plugin_bin(self):
        self.step("install", "--alias")
        self.assertIn("next", self.git("config", "--get", "alias.next").stdout)
        self.assertIn("board", self.git("config", "--get", "alias.board").stdout)
        self.git("checkout", "-q", "-b", "spike/x")
        self.commit("a")
        self.git("next")
        self.assertEqual(self.branch(), "wip/x")

    def test_install_skips_foreign_hook_and_still_marks_repo(self):
        self.git("config", "--unset", "branch-step.enabled")
        hook = self.work / ".git/hooks/pre-push"
        hook.write_text("#!/bin/sh\nexit 0\n")
        result = self.step("install")
        self.assertEqual(hook.read_text(), "#!/bin/sh\nexit 0\n", "上書きしない")
        self.assertIn("repo", result.stderr, "案内を出す")
        self.assertEqual(self.git("config", "--get", "branch-step.enabled").stdout.strip(), "true")

    def test_install_skips_repo_managed_hookspath(self):
        (self.work / ".githooks").mkdir()
        (self.work / ".githooks/pre-push").write_text("#!/bin/sh\nexit 0\n")
        self.git("config", "core.hooksPath", ".githooks")
        result = self.step("install")
        self.assertEqual((self.work / ".githooks/pre-push").read_text(), "#!/bin/sh\nexit 0\n")
        self.assertIn(".githooks", result.stderr)

    def test_install_no_hook_only_marks_repo(self):
        self.git("config", "--unset", "branch-step.enabled")
        self.step("install", "--no-hook")
        self.assertEqual(self.git("config", "--get", "branch-step.enabled").stdout.strip(), "true")
        self.assertFalse((self.work / ".git/hooks/pre-push").exists())

    # --- PATH 上の外部 subcommand（bin/git-next 等）と導入の印 ---

    def test_bin_git_next_runs_without_any_alias(self):
        self.assertNotEqual(self.git("config", "--get", "alias.next", check=False).returncode, 0)
        self.git("checkout", "-q", "-b", "spike/x")
        self.commit("a")
        self.git_bin("next")
        self.assertEqual(self.branch(), "wip/x")

    def test_bin_git_next_survives_alias_pointing_at_a_removed_plugin_version(self):
        """plugin を更新すると古いバージョンのフォルダは消える。alias がそこを指したままでも止まらない。"""
        self.git("config", "--unset", "branch-step.enabled")
        gone = "/nonexistent/chronista-style/0.0.1/skills/branch-step/scripts/branch-step"
        self.git("config", "alias.next", f'!"{gone}" next')
        self.git("checkout", "-q", "-b", "spike/x")
        self.commit("a")
        broken = self.git("next", check=False)
        self.assertNotEqual(broken.returncode, 0, "bin/ が PATH に無ければ、古い alias は今までどおり止まる")
        self.assertEqual(self.branch(), "spike/x")
        self.git_bin("next")
        self.assertEqual(self.branch(), "wip/x", "PATH 上の git-next が alias より先に動く。古い alias は導入の印として読む")

    def test_refuses_repo_that_never_installed_branch_step(self):
        self.git("config", "--unset", "branch-step.enabled")
        self.git("checkout", "-q", "-b", "spike/x")
        self.commit("a")
        for cmd in (["next"], ["keep"], ["drop"], ["board"]):
            result = self.git_bin(*cmd, check=False)
            self.assertNotEqual(result.returncode, 0, cmd)
            self.assertIn("branch-step install", result.stderr, cmd)
        self.assertEqual(self.branch(), "spike/x")
        self.assertIn("spike/x", self.local_branches())

    def test_bin_commands_run_from_a_subdirectory(self):
        self.git("checkout", "-q", "-b", "spike/x")
        self.commit("a", path="sub/dir/a.txt")
        self.git_bin("next", cwd=self.work / "sub/dir")
        self.assertEqual(self.branch(), "wip/x")
        board = self.git_bin("board", cwd=self.work / "sub/dir")
        self.assertIn("wip/x", board.stdout + board.stderr)

    def test_bin_ships_every_subcommand_and_the_installer(self):
        for name in ("git-next", "git-keep", "git-drop", "git-board", "branch-step"):
            self.assertTrue(os.access(BIN / name, os.X_OK), name)
        self.git("config", "--unset", "branch-step.enabled")
        env = {**self.env, "PATH": f"{BIN}{os.pathsep}{self.env['PATH']}"}
        subprocess.run(["branch-step", "install", "--no-hook"], cwd=self.work, env=env,
                       text=True, capture_output=True, check=True)
        self.assertEqual(self.git("config", "--get", "branch-step.enabled").stdout.strip(), "true")

    def test_pre_push_rejects_spike_and_allows_others(self):
        self.step("install")
        self.git("checkout", "-q", "-b", "spike/x")
        self.commit("a")
        result = self.git("push", "origin", "spike/x", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("spike", result.stderr)
        self.assertNotIn("spike/x", self.remote_branches())
        for src in ("spike/x", "HEAD", "@", "spike/x~0", "spike/x^{commit}"):
            result = self.git("push", "origin", f"{src}:refs/heads/wip/x", check=False)
            self.assertNotEqual(result.returncode, 0, f"spike を別名で押すのも拒否 ({src})")
        self.assertNotIn("wip/x", self.remote_branches())
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
