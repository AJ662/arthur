'use client'; // Required for client-side interactivity

import { useState } from 'react';
import axios from 'axios';

export default function Home() {
  const [agentName, setAgentName] = useState('');
  const [agentBehavior, setAgentBehavior] = useState('');
  const [response, setResponse] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await axios.post('http://localhost:8000/agents/', {
        name: agentName,
        behavior: agentBehavior,
        health: 100,
      });
      setResponse(res.data.message);
    } catch (err) {
      setResponse('Error creating agent');
    }
  };

  return (
    <main>
      <h1>Game Dev Kit Prototype</h1>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Agent Name"
          value={agentName}
          onChange={(e) => setAgentName(e.target.value)}
        />
        <input
          type="text"
          placeholder="Agent Behavior"
          value={agentBehavior}
          onChange={(e) => setAgentBehavior(e.target.value)}
        />
        <button type="submit">Create Agent</button>
      </form>
      {response && <p>{response}</p>}
    </main>
  );
}
