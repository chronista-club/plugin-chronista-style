#!/usr/bin/env ruby
# frozen_string_literal: true

# chronista-style SessionStart hook（Claude Code / Codex 共用）。
# git のプロジェクト情報と Atlas 候補を additionalContext で注入する。
# セッションは止めない。失敗したときは出せるものを出し、何がコケたかを systemMessage で知らせる。
Encoding.default_external = Encoding::UTF_8
require "json"
require "open3"

HOOK = "chronista-style session-start"
# ディレクトリ名・remote 名から外す接頭辞（例: claude-plugin-chronista-style → chronista-style）
PLUGIN_PREFIX = /\A(claude-plugin-|codex-plugin-|skillset-?|plugin-)/

# git が失敗した（リポジトリでない等）なら nil。git 自体が無ければ Errno::ENOENT が上がる
def git(dir, *args)
  out, status = Open3.capture2("git", "-C", dir, *args, err: File::NULL)
  status.success? ? out.strip : nil
end

# stdin の cwd がホストの契約。環境変数は旧経路の fallback
def project_dir(event)
  cwd = event["cwd"]
  dir = cwd.is_a?(String) && !cwd.empty? ? cwd : (ENV["CLAUDE_PROJECT_DIR"] || Dir.pwd)
  raise ArgumentError, "cwd が存在しません: #{dir}" unless File.directory?(dir)

  dir
end

def git_context(dir, warnings)
  branch = git(dir, "symbolic-ref", "--quiet", "--short", "HEAD") || git(dir, "rev-parse", "--verify", "--short", "HEAD")
  porcelain = git(dir, "status", "--porcelain=v1")
  {
    branch: branch || "-",
    last_commit: git(dir, "log", "-1", "--oneline") || "-",
    uncommitted: porcelain ? porcelain.lines.count.to_s : "-",
    remote_url: git(dir, "config", "--get", "remote.origin.url"),
  }
rescue Errno::ENOENT
  warnings << "git が見つかりません。ブランチ・commit・remote は省略"
  { branch: "-", last_commit: "-", uncommitted: "-", remote_url: nil }
end

# Atlas 候補: ディレクトリ名（そのまま / 接頭辞を外したもの）が主、remote のリポジトリ名が従
def atlas_candidates(project_name, remote_url)
  stripped = project_name.sub(PLUGIN_PREFIX, "")
  stripped = nil if stripped == project_name
  remote = nil
  if remote_url && !remote_url.empty?
    # https://github.com/org/repo(.git) と git@github.com:org/repo(.git) の両方
    remote = remote_url.sub(/\.git\z/, "").split(%r{[:/]}).last.to_s.sub(PLUGIN_PREFIX, "")
    remote = nil if remote.empty? || [project_name, stripped].include?(remote)
  end
  [[project_name, stripped].compact.join(" / "), remote]
end

def context(project_name, git, primary, remote)
  <<~MARKDOWN.chomp
    ## Chronista Session Context

    - Project dir: `#{project_name}`
    - Branch: `#{git[:branch]}`
    - Last commit: #{git[:last_commit]}
    - Uncommitted files: #{git[:uncommitted]}
    - Remote: `#{git[:remote_url] || "none"}`

    ### creo-memories

    - Context Engine の記憶コンテキストが実際に届いていれば重複検索は不要。未注入なら、接続済みの creo-memories の `search` で必要な記憶だけ補う。未接続なら作業は続け、記憶の取得・保存は未実施と報告する
    - `remember` / `create_todo` の Atlas 候補: `#{primary}`（remote 由来: `#{remote || "なし"}`）。exact match が無ければ、同じ repo の過去のアクション（todo）がある Atlas に倣う。前例も無ければ Personal に置いて一言添える。置き場で止まらない、聞かない

    ### 規律エッセンス（詳細は各スキル）

    - テストが先に失敗しない限り、プロダクションコードを書かない（`tdd`）
    - 根本原因を特定してから修正する（`systematic-debugging`）
    - 検証の証拠なしに完了を宣言しない。実機でしか確認できないものは「実機確認待ち」で止める（`verification`）
    - GO の前は自由な構想（Conception）。ユーザーが選ぶべき分岐があるときだけ短い方針提示 → GO。GO の後はその範囲を最後まで走り切る（`codeflow`）
    - 火花が降ったら `spark` スキル — 解釈ゼロで原文のまま pack。作業の範囲外の気づきも同じ
    - 穏やかに、真面目に、ユーモアを忘れずに。きつい言葉を使わず、事実は伝える（`chronista-style` 基本姿勢）

    その他の原則は `chronista-style` スキルを参照。
  MARKDOWN
end

def main
  warnings = []
  event = begin
    raw = $stdin.read.to_s
    raw.strip.empty? ? {} : JSON.parse(raw)
  rescue JSON::ParserError => e
    warnings << "stdin の JSON を読めません（#{e.message.lines.first.to_s.strip[0, 80]}）"
    {}
  end
  event = {} unless event.is_a?(Hash)

  dir = project_dir(event)
  name = File.basename(dir)
  git = git_context(dir, warnings)
  primary, remote = atlas_candidates(name, git[:remote_url])

  output = {
    "hookSpecificOutput" => { "hookEventName" => "SessionStart", "additionalContext" => context(name, git, primary, remote) },
  }
  output["systemMessage"] = "#{HOOK}: #{warnings.join('。')}" unless warnings.empty?
  puts JSON.generate(output)
rescue StandardError => e
  # context を組めなかった。セッションは止めず、何がコケたかだけ知らせる
  message = "#{HOOK}: #{e.message.lines.first.to_s.strip}"
  warn message
  puts JSON.generate("systemMessage" => message)
end

main
