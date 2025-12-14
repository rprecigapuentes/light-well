import { useState } from "react";

type AskBoxProps = {
  onAsk: (question: string) => void;
  answer: string | null;
};

export function AskBox({ onAsk, answer }: AskBoxProps) {
  const [question, setQuestion] = useState("");

  return (
    <div>
      <h3>Ask</h3>

      <textarea
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        rows={3}
        style={{ width: "100%" }}
      />

      <button
        onClick={() => onAsk(question)}
        disabled={!question.trim()}
      >
        Ask
      </button>

      {answer && (
        <div style={{ marginTop: "1rem" }}>
          <strong>Answer:</strong>
          <p>{answer}</p>
        </div>
      )}
    </div>
  );
}
