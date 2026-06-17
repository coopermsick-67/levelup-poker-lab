import type { DrillModule } from '../../types/drill'

interface Props {
  module: DrillModule
  onStart: (moduleId: string) => void
}

const difficultyColor: Record<string, string> = {
  Beginner: 'bg-green-600',
  Intermediate: 'bg-yellow-600',
  Advanced: 'bg-red-600',
}

export default function DrillCard({ module, onStart }: Props) {
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-xl p-5 flex flex-col gap-3 hover:border-gold transition-colors">
      <div className="flex items-start justify-between">
        <span className="text-3xl">{module.icon}</span>
        <span
          className={`text-xs font-bold px-2 py-0.5 rounded-full text-white ${difficultyColor[module.difficulty]}`}
        >
          {module.difficulty}
        </span>
      </div>
      <h3 className="text-lg font-bold text-gold">{module.title}</h3>
      <p className="text-sm text-gray-400 flex-1">{module.description}</p>
      <div className="flex items-center justify-between text-xs text-gray-500">
        <span>~{module.estimatedMinutes} min</span>
        <span>{module.drillCount} drills</span>
      </div>
      <button
        onClick={() => onStart(module.id)}
        className="w-full bg-felt hover:bg-felt-dark text-white font-bold py-2 rounded-lg transition-colors"
      >
        Start Drill
      </button>
    </div>
  )
}
