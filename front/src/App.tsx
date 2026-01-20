/* eslint-disable @typescript-eslint/no-unused-vars */
import { useState, useRef, useEffect } from 'react'
import { getChat, uploadFile } from '../services/chat.ts'
import { BACKEND_URL } from './const/const.ts';
import { io } from 'socket.io-client'; // 1. Importar el cliente
import './App.css'

type Role = 'user' | 'bot' | 'system'
type Message = { role: Role; text: string }

// 2. Definir la URL del backend (fuera del componente para evitar recrearlo)
const SOCKET_SERVER_URL = BACKEND_URL;

function App() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([])
  const endRef = useRef<HTMLDivElement | null>(null)

  // 3. Efecto para manejar la conexión de Socket.io
  useEffect(() => {
    const socket = io(SOCKET_SERVER_URL);

    // Escuchar el evento que configuramos en el backend (webhook-receiver)
    socket.on('file_notification', (data: { message: string, status: string }) => {
      console.log('Notificación recibida del servidor:', data);

      // Añadir el mensaje del bot automáticamente al chat
      setMessages((prev) => [...prev, {
        role: 'bot',
        text: data.message
      }]);
    });

    // Limpieza al desmontar el componente
    return () => {
      socket.disconnect();
    };
  }, []); // El array vacío asegura que solo se conecte una vez al cargar la app

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
      }
    } catch (err) {
      setMessages((m) => [...m, { role: 'bot', text: `could not connect to the server` }])
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
        // Mensaje del sistema local (opcional, ya que el bot hablará por el webhook)
        setMessages((m) => [...m, { role: 'system', text: `Uploading: ${res.filename || file.name}...` }])
      }
    } catch (err) {
      setMessages((m) => [...m, { role: 'system', text: `Network error uploading file` }])
    } finally {
      setLoading(false)
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
            <span className='load'>
              {loading ? '...' : '>'}
            </span>
          </button>

        </div>
      </div>
    </section>
  )
}

export default App
