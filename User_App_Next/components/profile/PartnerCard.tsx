// ABOUTME: Displays a single suggested partner card with level badge and schedule overlap message.
// ABOUTME: Shows player name, level/category, compatibility badge, and optional overlap time message.
import type { SuggestedPartner } from '@/types/database.types'

interface Props {
  partner: SuggestedPartner
}

export default function PartnerCard({ partner }: Props) {
  const { user, badge, overlapMessage } = partner

  return (
    <div className="p-4 border border-gray-200 rounded-lg bg-white space-y-1">
      <p className="font-medium text-gray-900">{user.full_name}</p>
      <p className="text-sm text-gray-500">
        {user.level_tier ?? '—'}{user.categoria ? ` / ${user.categoria}` : ''}
      </p>
      <span className={`inline-block text-xs font-medium px-2 py-0.5 rounded-full ${
        badge === 'nivel+horario'
          ? 'bg-green-100 text-green-700'
          : 'bg-blue-100 text-blue-700'
      }`}>
        {badge === 'nivel+horario' ? '🎾 Nivel + horario' : '📋 Solo nivel'}
      </span>
      {overlapMessage && (
        <p className="text-xs text-gray-500 italic">{overlapMessage}</p>
      )}
    </div>
  )
}
