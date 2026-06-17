import type { AnswerResponse } from '../../types/drill'

interface Props {
  result: AnswerResponse
  onNext: () => void
  isLast: boolean
}

export default function DrillFeedback({ result, onNext, isLast }: Props) {
  const color = result.correct ? 'text-green-400' : 'text-red-400'
  const borderColor = result.correct ? 'border-green-500' : 'border-red-500'
  const bgColor = result.correct ? 'bg-green-900/30' : 'bg-red-900/30'
  const icon = result.correct ? '✓' : '✗'
  const verdict = result.correct ? 'Correct!' : 'Incorrect'

  return (
    <div className={`mt-4 rounded-xl border ${borderColor} ${bgColor} p-5`}>
      <div className="flex items-center gap-2 mb-3">
        <span className={`text-xl font-bold ${color}`}>{icon}</span>
        <span className={`text-lg font-bold ${color}`}>{verdict}</span>
      </div>

      <div className="text-sm text-gray-300 space-y-2">
        <p>
          <span className="text-gray-500">Your answer:</span>{' '}
          <span className="font-medium">{result.user_answer_label || result.user_answer}</span>
        </p>
        {!result.correct && (
          <p>
            <span className="text-gray-500">Correct action:</span>{' '}
            <span className="font-medium text-green-400">{result.correct_action}</span>
          </p>
        )}
      </div>

      <div className="mt-4 bg-gray-900/50 rounded-lg p-3">
        <p className="text-sm text-gray-200 leading-relaxed">{result.feedback}</p>
      </div>

      <button
        onClick={onNext}
        className="mt-4 w-full bg-gold hover:bg-gold-dark text-gray-900 font-bold py-3 rounded-lg transition-colors"
      >
        {isLast ? 'View Results' : 'Next Drill →'}
      </button>
    </div>
  )
}
