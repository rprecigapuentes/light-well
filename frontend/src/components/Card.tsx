import React from "react";
import styles from "@/app/page.module.css";

interface CardProps {
  title?: string;
  children?: React.ReactNode;
  className?: string;
}

export default function Card({ title, children, className }: CardProps) {
  return (
    <div
      className={className}
      style={{
        background: "#fff",
        borderRadius: "8px",
        boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
        border: "1px solid #e5e7eb",
        padding: "1.5rem",
        height: "100%",
      }}
    >
      {title && <h3 className={styles.sectionTitle}>{title}</h3>}
      {children}
    </div>
  );
}
