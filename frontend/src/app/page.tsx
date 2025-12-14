"use client";

import React, { useEffect, useState, useCallback } from "react";
import styles from "./page.module.css";

import { bogotaDayRange } from "@/lib/time";
import { getDayData, getDayInsight, askDay } from "@/lib/api";

import type {
  DailyViewResponse,
  InsightResponse,
  AskResponse,
  TierResult,
  Features,
  L04Result,
  ISODate,
} from "@/lib/api/types";

import InsightBox from "@/components/InsightBox";
import AskBox from "@/components/AskBox";

// --- Helper Components ---

const StatItem = ({
  label,
  value,
  unit = "",
}: {
  label: string;
  value: string | number;
  unit?: string;
}) => (
  <div className={styles.statCard}>
    <span className={styles.statLabel}>{label}</span>
    <span className={styles.statValue}>
      {typeof value === "number"
        ? value.toLocaleString(undefined, { maximumFractionDigits: 2 })
        : value}
      {unit}
    </span>
  </div>
);

const ComplianceBadge = ({ compliant }: { compliant: boolean }) => (
  <span className={`${styles.badge} ${compliant ? styles.badgeSuccess : styles.badgeFailure}`}>
    {compliant ? "COMPLIANT" : "NON-COMPLIANT"}
  </span>
);

const TierCard = ({ title, tier }: { title: string; tier: TierResult }) => {
  return (
    <div
      className={styles.tierBox}
      style={{ borderColor: tier.compliant ? "#10b981" : "#ef4444" }}
    >
      <div className={styles.tierHeader}>
        <span className={styles.tierTitle}>{title}</span>
        <ComplianceBadge compliant={tier.compliant} />
      </div>

      <div className={styles.tierDetails}>
        <div className={styles.tierRow}>
          <span className={styles.tierRowLabel}>Threshold</span>
          <span className={styles.tierRowValue}>{tier.threshold}</span>
        </div>
        <div className={styles.tierRow}>
          <span className={styles.tierRowLabel}>Required Min</span>
          <span className={styles.tierRowValue}>{tier.required_minutes}m</span>
        </div>
        <div className={styles.tierRow}>
          <span className={styles.tierRowLabel}>Missing Min</span>
          <span
            className={styles.tierRowValue}
            style={{ color: tier.missing_minutes > 0 ? "#b91c1c" : "inherit" }}
          >
            {tier.missing_minutes}m
          </span>
        </div>
        <div className={styles.tierRow}>
          <span className={styles.tierRowLabel}>Best Continuous</span>
          <span className={styles.tierRowValue}>{tier.best_continuous_minutes}m</span>
        </div>
        <div className={styles.tierRow}>
          <span className={styles.tierRowLabel}>Max Gap</span>
          <span className={styles.tierRowValue}>{tier.max_gap_min}m</span>
        </div>
      </div>
    </div>
  );
};

export default function DailyViewPage() {
  // Default to today (Bogotá local date string); you can override in UI
  const [selectedDate, setSelectedDate] = useState<ISODate>(
    new Date().toISOString().split("T")[0] as ISODate
  );

  // Data States
  const [data, setData] = useState<DailyViewResponse | null>(null);
  const [loadingData, setLoadingData] = useState(false);
  const [dataError, setDataError] = useState<string | null>(null);

  // Insight States
  const [insight, setInsight] = useState<InsightResponse | null>(null);
  const [loadingInsight, setLoadingInsight] = useState(false);
  const [insightError, setInsightError] = useState<string | null>(null);

  // Ask States
  const [askResponse, setAskResponse] = useState<AskResponse | null>(null);
  const [loadingAsk, setLoadingAsk] = useState(false);
  const [askError, setAskError] = useState<string | null>(null);

  // Fetch Data & Insight when date changes
  const loadDay = useCallback(async (dateISO: ISODate) => {
    setLoadingData(true);
    setDataError(null);

    setLoadingInsight(true);
    setInsightError(null);

    setAskResponse(null); // Clear previous Q&A
    setAskError(null);

    const { startISO, endISO } = bogotaDayRange(dateISO);

    // 1) Fetch Main Data
    const dataRes = await getDayData(startISO, endISO);
    if (dataRes.ok) {
      setData(dataRes.data);
    } else {
      setDataError(dataRes.error);
      setData(null);
    }
    setLoadingData(false);

    // 2) Fetch Insight (always try; backend can decide if insufficient)
    const insightRes = await getDayInsight(startISO, endISO);
    if (insightRes.ok) {
      setInsight(insightRes.data);
    } else {
      setInsightError(insightRes.error);
      setInsight(null);
    }
    setLoadingInsight(false);
  }, []);

  useEffect(() => {
    loadDay(selectedDate);
  }, [loadDay, selectedDate]);

  const handleAsk = async (question: string) => {
    setLoadingAsk(true);
    setAskError(null);

    const { startISO, endISO } = bogotaDayRange(selectedDate);

    const res = await askDay(startISO, endISO, question);
    if (res.ok) {
      setAskResponse(res.data);
    } else {
      setAskError(res.error);
    }

    setLoadingAsk(false);
  };

  // Extract the specific day data (backend returns maps keyed by ISODate)
  const featuresForDay: Features | undefined = data?.features_by_day?.[selectedDate];
  const l04ForDay: L04Result | undefined = data?.l04_by_day?.[selectedDate];

  return (
    <main className={styles.main}>
      <header className={styles.header}>
        <h1 className={styles.title}>Daily View</h1>

        <div className={styles.controls}>
          <label htmlFor="date-picker">Select Date:</label>

          <input
            id="date-picker"
            type="date"
            className={styles.dateInput}
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value as ISODate)}
          />

          <button
            onClick={() => loadDay(selectedDate)}
            className={styles.askButton}
            style={{ padding: "0.5rem 1rem" }}
          >
            Refresh
          </button>
        </div>
      </header>

      {/* ERROR BANNER */}
      {dataError && (
        <div className={styles.errorBox}>
          <strong>Error loading data:</strong> {dataError}
        </div>
      )}

      {/* LOADING STATE */}
      {loadingData && (
        <div className={styles.loading}>Loading metrics for {selectedDate}...</div>
      )}

      {/* MAIN CONTENT */}
      {!loadingData && featuresForDay && l04ForDay && (
        <>
          {/* SECTION 1: EDI STATS (for selected day) */}
          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>EDI Statistics</h2>

            <div className={styles.statsGrid}>
              <StatItem label="Count" value={featuresForDay.count} />
              <StatItem label="Duration" value={featuresForDay.duration_s} unit="s" />
              <StatItem label="Mean" value={featuresForDay.edi_mean} />
              <StatItem label="Median" value={featuresForDay.edi_median} />
              <StatItem label="Min" value={featuresForDay.edi_min} />
              <StatItem label="Max" value={featuresForDay.edi_max} />
              <StatItem label="P10" value={featuresForDay.edi_p10} />
              <StatItem label="P90" value={featuresForDay.edi_p90} />
              <StatItem label="Last Value" value={featuresForDay.edi_last} />
              <StatItem label="Δ vs Median" value={featuresForDay.edi_delta_vs_median} />
            </div>
          </section>

          {/* SECTION 2: COMPLIANCE */}
          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>WELL L04 Compliance</h2>

            <div className={styles.tiersGrid}>
              <TierCard title="Tier 1" tier={l04ForDay.tier_1} />
              <TierCard title="Tier 2" tier={l04ForDay.tier_2} />
            </div>

            {l04ForDay.notes && (
              <div className={styles.notes}>
                <strong>Note:</strong> {l04ForDay.notes}
              </div>
            )}
          </section>

          {/* SECTION 3: INSIGHT & ASK */}
          <section className={`${styles.section} ${styles.interactionGrid}`}>
            <InsightBox isLoading={loadingInsight} insight={insight} error={insightError} />
            <AskBox
              onAsk={handleAsk}
              isLoading={loadingAsk}
              response={askResponse}
              error={askError}
            />
          </section>
        </>
      )}

      {/* EMPTY STATE */}
      {!loadingData && !dataError && (!featuresForDay || !l04ForDay) && (
        <div className={styles.loading}>No data available for {selectedDate}.</div>
      )}
    </main>
  );
}
