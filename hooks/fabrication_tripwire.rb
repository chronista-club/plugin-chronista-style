#!/usr/bin/env ruby
# frozen_string_literal: true

# Claude Code / Codex 共用の Stop hook。
# 最終メッセージに「ツール出力の形をした文」があるのに、セッションのどこにも対応する tool result が
# 無ければ block して、本物を実行させる。
# 判定できないとき（ログが読めない・形式が未知）は block しない。ただし黙らず、exit 1 + stderr で知らせる。
require "json"
require_relative "transcript"

# LANG=C の環境でも日本語の本文を UTF-8 として扱う。
# 実行時の代入は -w で警告が出て stderr の先頭行を汚すので、その間だけ黙らせる
verbose, $VERBOSE = $VERBOSE, nil
Encoding.default_external = Encoding::UTF_8
$VERBOSE = verbose

HOOK = "chronista-style fabrication-tripwire"

PATTERNS = [
  /test result:/,
  /[0-9]+ passed[;,]/,
  /all checks were successful/,
  /Squashed and merged/,
  /To github\.com/,
  /[0-9a-f]{7,12}\.\.[0-9a-f]{7,12}/,
  /File created successfully at/,
  /has been updated successfully/,
  /HEAD is now at/,
  %r{-> (origin/|FETCH_HEAD)},
].freeze

REASON_HEAD = "FABRICATION TRIPWIRE — the final message contains tool-output-shaped text " \
              "with NO matching tool result anywhere in this session:"
REASON_TAIL = "Run the real tool and quote its ACTUAL output, or delete the unbacked text. " \
              "For deliberate example quotations, add TRIPWIRE-ACK on a line by itself. " \
              "Never report a result you did not observe."

# => block の指示（Hash）か nil
def check(event)
  # 差し戻しは 1 ターンに 1 回。どちらのホストもループに落とさない
  return nil if event["stop_hook_active"] == true

  # Codex は transcript_path を string | null と定義する。無ければ検査できないが、異常ではない
  path = event.fetch("transcript_path")
  return nil if path.nil?

  prose, tools = begin
    Transcript.read(path)
  rescue Transcript::OpaqueEvidence
    # Codex はツール出力を暗号化して保存することがある。読めない証拠がある間は判定しない（異常ではない）
    return nil
  end
  prose = event["last_assistant_message"] if event["last_assistant_message"].is_a?(String)
  return nil if prose.split(/\R/).include?("TRIPWIRE-ACK")

  violations = PATTERNS.map do |pattern|
    match = pattern.match(prose)
    next unless match && !pattern.match?(tools)

    %(  - "#{match[0]}" [#{pattern.source}])
  end.compact
  return nil if violations.empty?

  { "decision" => "block", "reason" => [REASON_HEAD, *violations, REASON_TAIL].join("\n") }
end

def main
  event = JSON.parse($stdin.read.to_s.scrub)
  raise ArgumentError, "stdin の JSON がオブジェクトではありません（#{event.class}）" unless event.is_a?(Hash)

  result = check(event)
  puts JSON.generate(result) if result
rescue StandardError => e
  # block しない（stdout 無し）。non-zero exit でホストが hook error を出し、stderr の先頭行が通知に載る。
  # 先頭行は一行・短く（Ruby 2.6 の json は壊れた行を丸ごとメッセージに入れる）
  warn "#{HOOK}: skipped — #{e.class}: #{e.message.to_s.scrub.lines.first.to_s.strip[0, 160]}"
  exit 1
end

main
