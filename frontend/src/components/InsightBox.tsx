import React from "react";
import Card from "@/components/Card";
import styles from "@/app/page.module.css";

import type { InsightResponse, LLMOutput } from "@/lib/api/types";

interface InsightBoxProps {
  isLoading: boolean;
  insight: InsightResponse | null;
  error?: string | null;
}

function llmToText(output: LLMOutput): string {
  if (typeof output === "string") return output;

  if (output && typeof output === "object") {
    const obj = output as Record<string, unknown>;
    const parts: string[] = [];

    const summary = obj["summary"];
    if (typeof summary === "string" && summary.trim()) {
      parts.push(`Summary:\n${summary}`);
    }

    const answer = obj["answer"];
    if (typeof answer === "string" && answer.trim()) {
      parts.push(`Answer:\n${answer}`);
    }

    const recs = obj["recommendations"];
    if (Array.isArray(recs)) {
      const items = recs.filter((x) => typeof x === "string") as string[];
      if (items.length) {
        parts.push(`Recommendations:\n- ${items.join("\n- ")}`);
      }
    }

    const notes = obj["notes"];
    if (typeof notes === "string" && notes.trim()) {
      parts.push(`Notes:\n${notes}`);
    }

    if (parts.length > 0) return parts.join("\n\n");
    return JSON.stringify(obj, null, 2);
  }

  return String(output);
}

export default function InsightBox({ isLoading, insight, error }: InsightBoxProps) {
  let content: React.ReactNode;

  if (isLoading) {
    content = <div className={styles.loading}>Generating daily insight...</div>;
  } else if (error) {
    content = <div className={styles.errorBox}>{error}</div>;
  } else if (!insight) {
    content = <div style={{ color: "#9ca3af" }}>No insight data available.</div>;
  } else {
    content = <div className={styles.answerArea}>{llmToText(insight.llm)}</div>;
  }

  return <Card title="AI Insight">{content}</Card>;
}
