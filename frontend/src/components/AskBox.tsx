import React, { useState } from "react";
import Card from "@/components/Card";
import styles from "@/app/page.module.css";
import type { AskResponse, LLMOutput } from "@/lib/api/types";

interface AskBoxProps {
  onAsk: (question: string) => Promise<void>;
  response: AskResponse | null;
  isLoading: boolean;
  error?: string | null;
}

function llmToText(output: LLMOutput): string {
  if (typeof output === "string") return output;

  if (output && typeof output === "object") {
    const obj = output as Record<string, unknown>;
    const parts: string[] = [];

    const answer = obj["answer"];
    if (typeof answer === "string" && answer.trim()) parts.push(answer);

    const summary = obj["summary"];
    if (typeof summary === "string" && summary.trim()) parts.push(`Summary: ${summary}`);

    const notes = obj["notes"];
    if (typeof notes === "string" && notes.trim()) parts.push(`Note: ${notes}`);

    const recs = obj["recommendations"];
    if (Array.isArray(recs)) {
      const items = recs.filter((x) => typeof x === "string") as string[];
      if (items.length) parts.push(`Recommendations:\n- ${items.join("\n- ")}`);
    }

    if (parts.length > 0) return parts.join("\n\n");
    return JSON.stringify(obj, null, 2);
  }

  return String(output);
}

export default function AskBox({ onAsk, response, isLoading, error }: AskBoxProps) {
  const [question, setQuestion] = useState("");
  const [lastAsked, setLastAsked] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const q = question.trim();
    if (!q || isLoading) return;

    setLastAsked(q);
    await onAsk(q);
  };

  return (
    <Card title="Ask AI about this day">
      <form onSubmit={handleSubmit} className={styles.askInputGroup}>
        <textarea
          className={styles.askInput}
          placeholder="e.g. Why was Tier 1 non-compliant?"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          disabled={isLoading}
          rows={3}
        />
        <button type="submit" className={styles.askButton} disabled={isLoading || !question.trim()}>
          {isLoading ? "Asking..." : "Ask"}
        </button>
      </form>

      {error && <div className={styles.errorBox}>{error}</div>}

      {response && (
        <div className={styles.answerArea}>
          <strong>Q: {response.question ?? lastAsked ?? question.trim()}</strong>
          <div style={{ marginTop: "0.5rem" }}>{llmToText(response.llm)}</div>
        </div>
      )}
    </Card>
  );
}
