import { useState, useRef, useEffect } from 'react'
import { getChat, uploadFile } from '../services/chat.ts'
import './App.css'

type Role = 'user' | 'bot' | 'system'
type Message = { role: Role; text: string }



function App() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([])
  const endRef = useRef<HTMLDivElement | null>(null)


  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function sendMessage() {
    const text = input.trim()
    if (!text) return
    const userMsg: Message = { role: 'user', text }
    setMessages((m) => [...m, userMsg])
    setInput('')
    setLoading(true)
    try {
      const data = await getChat(text)
      if ( data.reply) {
        setMessages((m) => [...m, { role: 'bot', text: data.reply }])
      } else {
        console.log('Server error:', data)
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err)
      setMessages((m) => [...m, { role: 'bot', text: `could not connect to the server` }])
      console.error('Network error:', msg)
    } finally {
      setLoading(false)
    }
  }

  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const files = e.target.files
    if (!files || files.length === 0) return
    const file = files[0]
    setLoading(true)
    try {
      const res = await uploadFile(file)
      if (res && res.ok) {
        setUploadedFiles((s) => [...s, res.filename || file.name])
        setMessages((m) => [...m, { role: 'system', text: `Archivo cargado: ${res.filename || file.name}` }])
      } else {
        setMessages((m) => [...m, { role: 'system', text: `Error al subir: ${JSON.stringify(res)}` }])
      }
    } catch (err) {
      setMessages((m) => [...m, { role: 'system', text: `Error de red al subir archivo` }])
      console.error(err)
    } finally {
      setLoading(false)
      // clear the input value so same file can be reselected
      e.currentTarget.value = ''
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter') sendMessage()
  }

  return (
    <section className='chat'>
      <div className="app-container">
        <h1>Chat bot</h1>
        <div className="chat-window">
          {messages.length === 0 && <div className="msg_system">Hi, how may I assist you today?</div>}
          {messages.map((m, i) => (
            <div key={i} className={`msg_${m.role}`}>
              <span>{m.text}</span>
            </div>
          ))}
          <div ref={endRef} />
        </div>

        <div className="composer">
          <input
            value={input}
            className='input-chat'
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Try asking me anything..."
            disabled={loading}
          />
          <label className='upload-file-buttom'> <span >+
            <input className='input-file' type="file" onChange={handleFileChange} />
          </span>
          </label>
          <button onClick={sendMessage} disabled={loading}>
            <span>
              {loading ? '...' : '>'}
            </span>
          </button>

        </div>
      </div>
    </section>
  )
}

export default App
