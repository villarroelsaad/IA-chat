import { BACKEND_URL } from '../src/const/const.ts';

export const getChat = async (text: string) => { 
    const chat = await fetch(`${BACKEND_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
      })
    const data = await chat.json();
    return data;
    
    
}

export const uploadFile = async (file: File) => {
  const fd = new FormData();
  fd.append('file', file);

  const res = await fetch(`${BACKEND_URL}/upload-file`, {
    method: 'POST',
    body: fd,
  });
  return res.json();
}