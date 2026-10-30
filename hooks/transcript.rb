# frozen_string_literal: true

# Claude の JSONL と Codex の rollout JSONL を同じ形に読む。ログの schema は安定していない。
#
# 証拠になるのは実際の tool result の記録だけ。prompt・推論・要約・tool 呼び出しの引数は
# 証拠にならない。元の tripwire と同じく、証拠はセッション全体、報告は最新のもの。
# 判定に関わる壊れた入力は、途中まで読んだ証拠で判定せず UnknownFormat にする（知らせるのは呼び手）。
# 読めない証拠（Codex が暗号化して保存したツール出力）は OpaqueEvidence にする — 判定できないが異常ではない。
require "json"

module Transcript
  class UnknownFormat < StandardError; end
  class OpaqueEvidence < StandardError; end

  TEXT_TYPES = %w[text input_text output_text].freeze
  # 本文を持たないが正規のブロック。tool_reference は ToolSearch の結果（型名とツール名だけ）
  KNOWN_BLOCK_TYPES = (TEXT_TYPES + %w[
    image input_image image_url audio input_audio resource resource_link
    tool_use tool_reference thinking redacted_thinking
  ]).freeze

  # content は文字列か、型付きブロックの配列。知らない型のブロックが混ざっていたら読まない
  def self.text_content(value)
    return value if value.is_a?(String)
    raise UnknownFormat, "unknown text content shape: #{value.class}" unless value.is_a?(Array)

    value.each do |block|
      next if block.is_a?(Hash) && KNOWN_BLOCK_TYPES.include?(block["type"])

      raise UnknownFormat, "unknown content block: #{block.is_a?(Hash) ? block['type'].inspect : block.class}"
    end
    value.select { |block| TEXT_TYPES.include?(block["type"]) && block["text"].is_a?(String) }
         .map { |block| block["text"] }
         .join("\n")
  end

  def self.opaque?(value)
    value.is_a?(Array) && value.any? { |block| block.is_a?(Hash) && block["type"] == "encrypted_content" }
  end

  # => [prose, tools]
  #   prose: 現在ターンの最終 assistant メッセージ（新しい prompt が来たら空に戻す）
  #   tools: セッション全体の tool result を改行で連結
  def self.read(path)
    prose = ""
    tools = []
    formats = {}
    File.foreach(path, encoding: "UTF-8") do |line|
      next if line.strip.empty?

      row = JSON.parse(line)
      raise UnknownFormat, "transcript row is not an object: #{row.class}" unless row.is_a?(Hash)

      case row["type"]
      when "user", "assistant"
        formats["claude"] = true
        prose = read_claude(row, prose, tools)
      when "response_item"
        formats["codex"] = true
        prose = read_codex(row.fetch("payload"), prose, tools)
      when "event_msg"
        prose = "" if row.dig("payload", "type") == "task_started"
      end
    end
    raise UnknownFormat, "unknown or mixed transcript format: #{formats.keys.inspect}" unless formats.size == 1

    [prose, tools.join("\n")]
  end

  def self.read_claude(row, prose, tools)
    content = row.fetch("message").fetch("content")
    if row["type"] == "assistant"
      text = text_content(content)
      return text.empty? ? prose : text
    end

    results = content.is_a?(Array) ? content.select { |block| block.is_a?(Hash) && block["type"] == "tool_result" } : []
    if results.any?
      tools.concat(results.map { |block| text_content(block.fetch("content")) })
      prose
    elsif text_content(content).start_with?("Stop hook feedback:")
      prose
    else
      ""
    end
  end

  def self.read_codex(item, prose, tools)
    type = item.fetch("type")
    if %w[function_call_output custom_tool_call_output].include?(type)
      output = item.fetch("output")
      raise OpaqueEvidence, "encrypted tool output" if opaque?(output)

      tools << text_content(output)
      prose
    elsif type == "message"
      case item.fetch("role")
      when "user" then ""
      when "assistant"
        # commentary は最終報告ではない
        [nil, "final", "final_answer"].include?(item["phase"]) ? text_content(item.fetch("content")) : prose
      else prose
      end
    elsif type.end_with?("_output")
      raise UnknownFormat, "unknown Codex output record: #{type}"
    else
      prose
    end
  end
end
