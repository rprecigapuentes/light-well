"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import styles from "./page.module.css";

import { bogotaDayRange } from "@/lib/time";
import { getDayData, getDayInsight, askDay } from "@/lib/api";

import { DaySelector } from "@/components/DaySelector";
import { Card } from "@/components/Card";
import { InsightBox } from "@/components/InsightBox";
import { AskBox } from "@/components/AskBox";

import type { DailyViewResponse, LLMOutput, ISODate } from "@/lib/api/types";

function llmToText(llm: LLMOutput): string | null {
  if (typeof llm === "string") return llm;

  if (llm && typeof llm === "object") {
    const obj = llm as Record<string, unknown>;
    const parts: string[] = [];

    const summary = obj["summary"];
    if (typeof summary === "string" && summary.trim()) {
      parts.push(`Summary:\n${summary}`);
    }

    const recs = obj["recommendations"];
    if (Array.isArray(recs)) {
      const items = recs.filter((x) => typeof x === "string") as string[];
      if (items.length > 0) {
        parts.push(`Recommendations:\n- ${items.join("\n- ")}`);
      }
    }

    const answer = obj["answer"];
    if (typeof answer === "string" && answer.trim()) {
      parts.push(`Answer:\n${answer}`);
    }

    const notes = obj["notes"];
    if (typeof notes === "string" && notes.trim()) {
      parts.push(`Notes:\n${notes}`);
    }

    if (parts.length > 0) return parts.join("\n\n");

    // Fallback: si el JSON viene con otro shape
    return JSON.stringify(obj, null, 2);
  }

  return null;
}

export default function Home() {
  const [date, setDate] = useState<ISODate>("2025-12-13");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [data, setData] = useState<DailyViewResponse | null>(null);
  const [insightText, setInsightText] = useState<string | null>(null);
  const [answerText, setAnswerText] = useState<string | null>(null);

  useEffect(() => {
    async function loadDay() {
      setLoading(true);
      setError(null);
      setAnswerText(null);

      const { startISO, endISO } = bogotaDayRange(date);

      const result = await getDayData(startISO, endISO);

      if (!result.ok) {
        setError(result.error);
        setData(null);
        setInsightText(null);
        setLoading(false);
        return;
      }

      setData(result.data);

      // Tu "count" está dentro de features_global (según lo que mostrabas en UI)
      if (result.data.features_global.count > 0) {
        const insightResult = await getDayInsight(startISO, endISO);
        if (insightResult.ok) {
          setInsightText(llmToText(insightResult.data.llm));
        } else {
          setInsightText(null);
        }
      } else {
        setInsightText(null);
      }

      setLoading(false);
    }

    loadDay();
  }, [date]);

  async function handleAsk(question: string) {
    if (!data || data.features_global.count === 0) return;

    const { startISO, endISO } = bogotaDayRange(date);

    const result = await askDay(startISO, endISO, question);

    if (result.ok) {
      setAnswerText(llmToText(result.data.llm));
    } else {
      setAnswerText(result.error);
    }
  }

  const hasData = !!data && data.features_global.count > 0;

  return (
    <div className={styles.page}>
      <main className={styles.main}>
        <Image
          className={styles.logo}
          src="/next.svg"
          alt="Next.js logo"
          width={100}
          height={20}
          priority
        />

        <h1>LightWell — Daily View</h1>

        <DaySelector value={date} onChange={setDate} />

        {loading && <p>Loading…</p>}

        {!loading && error && (
          <p style={{ color: "red" }}>
            <strong>Error:</strong> {error}
          </p>
        )}

        {!loading && data && !hasData && <p>No data available for this day.</p>}

        {!loading && hasData && (
          <>
            <Card title="Global metrics">
              <pre>{JSON.stringify(data.features_global, null, 2)}</pre>
              <pre>{JSON.stringify(data.l04_global, null, 2)}</pre>
            </Card>

            <Card title="By-day metrics">
              <pre>{JSON.stringify(data.features_by_day, null, 2)}</pre>
              <pre>{JSON.stringify(data.l04_by_day, null, 2)}</pre>
            </Card>

            <Card title="Insight">
              <InsightBox text={insightText} />
            </Card>

            <Card title="Ask">
              <AskBox onAsk={handleAsk} answer={answerText} />
            </Card>
          </>
        )}
      </main>
    </div>
  );
}
