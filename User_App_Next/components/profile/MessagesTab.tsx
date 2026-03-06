// ABOUTME: Messages tab — shows conversation list and in-tab thread view.
// ABOUTME: Fetches GET /api/messages on mount. Clicking a conversation loads the thread.
'use client'

import { useState, useEffect, useRef } from 'react'
import type { Conversation, DirectMessage } from '@/types/database.types'
import MessageCompose from './MessageCompose'

function formatTime(iso: string): string {
  const d = new Date(iso)
  const now = new Date()
  const isToday = d.toDateString() === now.toDateString()
  if (isToday) {
    return d.toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit', hour12: true })
  }
  return d.toLocaleDateString('es-CO', { day: 'numeric', month: 'short' })
}

interface Props {
  currentUserId: string
}

export default function MessagesTab({ currentUserId }: Props) {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [loading, setLoading] = useState(true)
  const [activeConv, setActiveConv] = useState<Conversation | null>(null)
  const [thread, setThread] = useState<DirectMessage[]>([])
  const [loadingThread, setLoadingThread] = useState(false)
  const [composingNew, setComposingNew] = useState(false)
  const threadBottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    fetchConversations()
  }, [])

  useEffect(() => {
    threadBottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [thread])

  async function fetchConversations() {
    setLoading(true)
    const res = await fetch('/api/messages')
    if (res.ok) {
      const data = await res.json()
      setConversations(data.conversations || [])
    }
    setLoading(false)
  }

  async function openConversation(conv: Conversation) {
    setActiveConv(conv)
    setLoadingThread(true)
    const res = await fetch(`/api/messages/${conv.other_user.id}`)
    if (res.ok) {
      const data = await res.json()
      setThread(data.messages || [])
      // Clear unread badge locally
      setConversations(prev =>
        prev.map(c => c.other_user.id === conv.other_user.id ? { ...c, unread_count: 0 } : c)
      )
    }
    setLoadingThread(false)
  }

  function handleReplySent() {
    if (activeConv) openConversation(activeConv)
    setComposingNew(false)
  }

  if (loading) {
    return <p className="text-sm text-gray-500">Cargando mensajes...</p>
  }

  // Thread view
  if (activeConv) {
    return (
      <div className="space-y-4">
        <button
          onClick={() => { setActiveConv(null); setThread([]) }}
          className="text-sm text-us-open-light-blue hover:underline"
        >
          &larr; Volver a conversaciones
        </button>

        <div className="flex items-center justify-between">
          <div>
            <p className="font-semibold text-us-open-blue">{activeConv.other_user.full_name}</p>
            <p className="text-xs text-gray-500">
              {activeConv.other_user.level_tier ?? '—'}
              {activeConv.other_user.categoria ? ` / ${activeConv.other_user.categoria}` : ''}
            </p>
          </div>
          <button
            onClick={() => setComposingNew(true)}
            className="px-3 py-1.5 text-xs bg-us-open-blue text-white rounded-lg font-medium hover:bg-us-open-light-blue transition-colors"
          >
            Responder
          </button>
        </div>

        <div className="border border-gray-200 rounded-lg bg-gray-50 p-4 space-y-3 max-h-96 overflow-y-auto">
          {loadingThread ? (
            <p className="text-sm text-gray-400 text-center">Cargando...</p>
          ) : thread.length === 0 ? (
            <p className="text-sm text-gray-400 text-center">Sin mensajes aún.</p>
          ) : (
            thread.map(msg => {
              const isMe = msg.sender_id === currentUserId
              return (
                <div key={msg.id} className={`flex ${isMe ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-xs px-3 py-2 rounded-xl text-sm ${
                    isMe
                      ? 'bg-us-open-blue text-white'
                      : 'bg-white border border-gray-200 text-gray-800'
                  }`}>
                    <p>{msg.content}</p>
                    <p className={`text-xs mt-1 ${isMe ? 'text-blue-200' : 'text-gray-400'}`}>
                      {formatTime(msg.created_at)}
                    </p>
                  </div>
                </div>
              )
            })
          )}
          <div ref={threadBottomRef} />
        </div>

        {composingNew && (
          <MessageCompose
            recipientId={activeConv.other_user.id}
            recipientName={activeConv.other_user.full_name}
            onClose={() => setComposingNew(false)}
            onSent={handleReplySent}
          />
        )}
      </div>
    )
  }

  // Conversation list view
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-us-open-blue">Mensajes</h3>

      {conversations.length === 0 ? (
        <p className="text-sm text-gray-500">
          Aún no tienes mensajes. Puedes escribirle a un jugador desde la pestaña Comunidad.
        </p>
      ) : (
        <div className="space-y-2">
          {conversations.map(conv => (
            <button
              key={conv.other_user.id}
              onClick={() => openConversation(conv)}
              className="w-full text-left p-4 border border-gray-200 rounded-lg bg-white hover:bg-gray-50 transition-colors space-y-0.5"
            >
              <div className="flex justify-between items-start">
                <p className={`font-medium text-gray-900 ${conv.unread_count > 0 ? 'font-semibold' : ''}`}>
                  {conv.other_user.full_name}
                </p>
                <div className="flex items-center gap-2 flex-shrink-0">
                  <span className="text-xs text-gray-400">
                    {formatTime(conv.last_message.created_at)}
                  </span>
                  {conv.unread_count > 0 && (
                    <span className="bg-us-open-light-blue text-white text-xs font-bold px-1.5 py-0.5 rounded-full">
                      {conv.unread_count}
                    </span>
                  )}
                </div>
              </div>
              <p className="text-sm text-gray-500 truncate">{conv.last_message.content}</p>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
