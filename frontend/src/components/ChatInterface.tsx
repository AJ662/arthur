'use client';

import { useState, useEffect, useRef } from 'react';

interface Message {
  id: string;
  sender: 'player' | 'bot';
  sender_name: string;
  content: string;
  timestamp: string;
  bot_id?: string;
}

interface ChatInterfaceProps {
  gameId: string;
}

export default function ChatInterface({ gameId }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [activeBots, setActiveBots] = useState<any[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (gameId) {
      loadConversation();
    }
  }, [gameId]);

  const loadConversation = async () => {
    try {
      const response = await fetch(`http://localhost:8000/games/${gameId}/conversation`);
      const data = await response.json();
      setMessages(data.conversation || []);
      setActiveBots(data.active_bots || []);
    } catch (error) {
      console.error('Failed to load conversation:', error);
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || !gameId) return;

    setIsLoading(true);
    const messageToSend = inputMessage;
    setInputMessage('');

    try {
      const response = await fetch(`http://localhost:8000/games/${gameId}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: messageToSend,
          game_id: gameId,
          player_id: 'player1'
        })
      });

      if (!response.ok) throw new Error('Failed to send message');
      
      const data = await response.json();
      
      // Add player message and bot responses
      const newMessages = [data.player_message, ...data.bot_responses];
      setMessages(prev => [...prev, ...newMessages]);

    } catch (error) {
      console.error('Chat error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleBot = async (botId: string) => {
    try {
      await fetch(`http://localhost:8000/games/${gameId}/bots/${botId}/toggle`, {
        method: 'PUT'
      });
      loadConversation(); // Reload to get updated bot status
    } catch (error) {
      console.error('Failed to toggle bot:', error);
    }
  };

  return (
    <div className="flex h-96">
      {/* Bot Panel */}
      <div className="w-64 bg-gray-50 border-r p-4">
        <h4 className="font-semibold mb-3">Active Bots</h4>
        <div className="space-y-2">
          {activeBots.map((bot) => (
            <div key={bot.id} className="flex items-center justify-between p-2 bg-white rounded border">
              <span className="text-sm font-medium">{bot.name}</span>
              <button
                onClick={() => toggleBot(bot.id)}
                className="text-xs px-2 py-1 bg-green-100 text-green-800 rounded"
              >
                Active
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col bg-white">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.sender === 'player' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-md px-4 py-2 rounded-lg ${
                  message.sender === 'player'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-900 border-l-4 border-purple-500'
                }`}
              >
                {message.sender === 'bot' && (
                  <div className="text-xs font-semibold text-purple-600 mb-1">
                    {message.sender_name}
                  </div>
                )}
                <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                <p className="text-xs opacity-75 mt-1">
                  {new Date(message.timestamp).toLocaleTimeString()}
                </p>
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-yellow-100 border border-yellow-300 text-yellow-800 px-4 py-2 rounded-lg">
                <div className="flex items-center space-x-2">
                  <div className="animate-spin w-4 h-4 border-2 border-yellow-600 border-t-transparent rounded-full"></div>
                  <span>All bots are thinking...</span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <form onSubmit={handleSendMessage} className="p-4 border-t">
          <div className="flex space-x-2">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Speak to all bots..."
              className="flex-1 px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={isLoading || !inputMessage.trim()}
              className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              Send to All
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}