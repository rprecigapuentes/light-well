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

function llmToText(llm: unknown): string | null {
  if (typeof llm === "string") return llm;

  if (llm && typeof llm === "object") {
    const obj = llm as any;

    const parts: string[] = [];

    if (obj.summary) parts.push(`Summary:\n${obj.summary}`);
    if (obj.recommendations) parts.push(`Recommendations:\n${obj.recommendations}`);
    if (obj.answer) parts.push(`Answer:\n${obj.answer}`);
    if (obj.notes) parts.push(`Notes:\n${obj.notes}`);

    if (parts.length > 0) return parts.join("\n\n");

    // Fallback for unknown shapes
    return JSON.stringify(obj, null, 2);
  }

  return null;
}

export default function Home() {
  // -----------------------------
  // State
  // -----------------------------
  const [date, setDate] = useState("2025-12-13");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [data, setData] = useState<any | null>(null);
  const [insightText, setInsightText] = useState<string | null>(null);
  const [answerText, setAnswerText] = useState<string | null>(null);

  // -----------------------------
  // Load data when date changes
  // -----------------------------
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

      // If there is data, fetch insight
      if (result.data.count > 0) {
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

  // -----------------------------
  // Ask handler
  // -----------------------------
  async function handleAsk(question: string) {
    if (!data || data.count === 0) return;

    const { startISO, endISO } = bogotaDayRange(date);

    const result = await askDay(startISO, endISO, question);

    if (result.ok) {
      setAnswerText(llmToText(result.data.llm));
    } else {
      setAnswerText(result.error);
    }
  }

  // -----------------------------
  // Render
  // -----------------------------
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

        {!loading && data && data.count === 0 && (
          <p>No data available for this day.</p>
        )}

        {!loading && data && data.count > 0 && (
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
