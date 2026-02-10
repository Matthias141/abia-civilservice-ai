"use client";

interface SuggestedQuestionsProps {
  questions: string[];
  onSelect: (question: string) => void;
}

export default function SuggestedQuestions({
  questions,
  onSelect,
}: SuggestedQuestionsProps) {
  if (questions.length === 0) return null;

  return (
    <div className="mb-6">
      <p className="text-xs text-gray-400 mb-3 text-center">
        Try asking about:
      </p>
      <div className="flex flex-wrap justify-center gap-2">
        {questions.map((q, i) => (
          <button
            key={i}
            onClick={() => onSelect(q)}
            className="text-xs bg-white border border-gray-200 text-gray-600 px-3 py-2 rounded-full hover:bg-green-50 hover:border-green-300 hover:text-green-700 transition-colors"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}
