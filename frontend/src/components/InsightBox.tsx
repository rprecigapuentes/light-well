type InsightBoxProps = {
  text: string | null;
};

export function InsightBox({ text }: InsightBoxProps) {
  if (!text) {
    return <p>No insight available.</p>;
  }

  return (
    <div>
      <h3>Insight</h3>
      <p>{text}</p>
    </div>
  );
}
