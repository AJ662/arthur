'use client';

import { useState } from 'react';
import GameCreator from './GameCreators'
import ChatInterface from './ChatInterface';
import { gameAPI } from '@/lib/api';

export default function GameDashboard() {
  const [currentGame, setCurrentGame] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'create' | 'play' | 'manage'>('create');

  const handleGameCreated = (gameId: string) => {
    setCurrentGame(gameId);
    setActiveTab('play');
  };

  const handlePlayerAction = async (action: string) => {
    if (!currentGame) return;

    try {
      await gameAPI.sendPlayerAction(currentGame, {
        type: action,
        player_id: 'user_123',
        timestamp: new Date().toISOString(),
      });
    } catch (error) {
      console.error('Action failed:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <h1 className="text-3xl font-bold text-gray-900">Game Development Kit</h1>
          <p className="text-gray-600">Powered by Google Gemini AI & Event-Driven Architecture</p>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex space-x-8">
            {[
              { id: 'create', label: 'Create Game', icon: '🎮' },
              { id: 'play', label: 'Play Game', icon: '🕹️' },
              { id: 'manage', label: 'Manage', icon: '⚙️' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`py-4 px-2 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.icon} {tab.label}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {activeTab === 'create' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <GameCreator onGameCreated={handleGameCreated} />
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold mb-4">Module Architecture</h3>
              <div className="space-y-3">
                {[
                  { name: 'LLM Chatbot', status: 'active', description: 'Google Gemini 2.0 Flash integration' },
                  { name: 'State Management', status: 'active', description: 'Redis-backed persistence' },
                  { name: 'Rule Engine', status: 'active', description: 'Dynamic game rules' },
                  { name: 'Event System', status: 'active', description: 'FastStream event-driven' },
                ].map((module) => (
                  <div key={module.name} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                    <div>
                      <div className="font-medium">{module.name}</div>
                      <div className="text-sm text-gray-600">{module.description}</div>
                    </div>
                    <span className={`px-2 py-1 text-xs rounded ${
                      module.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {module.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'play' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Game Area */}
            <div className="lg:col-span-2 space-y-6">
              {currentGame ? (
                <>
                  <div className="bg-white rounded-lg shadow-md p-6">
                    <h3 className="text-xl font-semibold mb-4">Game: {currentGame}</h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      {['Explore', 'Inventory', 'Stats', 'Save'].map((action) => (
                        <button
                          key={action}
                          onClick={() => handlePlayerAction(action.toLowerCase())}
                          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                        >
                          {action}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="bg-white rounded-lg shadow-md p-6">
                    <h4 className="text-lg font-medium mb-4">Game State</h4>
                    <div className="bg-gray-50 p-4 rounded text-sm font-mono">
                      {JSON.stringify({
                        gameId: currentGame,
                        status: 'active',
                        player: { health: 100, level: 1, inventory: ['sword', 'potion'] }
                      }, null, 2)}
                    </div>
                  </div>
                </>
              ) : (
                <div className="bg-white rounded-lg shadow-md p-6 text-center">
                  <p className="text-gray-500">Create a game first to start playing!</p>
                </div>
              )}
            </div>

            {/* Chat Interface */}
            <div className="lg:col-span-1">
              <ChatInterface gameId={currentGame || undefined} playerId="user_123" />
            </div>
          </div>
        )}

        {activeTab === 'manage' && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-semibold mb-4">System Management</h3>
            <div className="space-y-4">
              <div className="p-4 bg-green-50 rounded">
                <h4 className="font-medium text-green-800">✅ All Systems Operational</h4>
                <p className="text-green-700 text-sm">Event-driven architecture running smoothly</p>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 border rounded">
                  <h5 className="font-medium">Redis Events</h5>
                  <p className="text-sm text-gray-600">Event broker status: Connected</p>
                </div>
                <div className="p-4 border rounded">
                  <h5 className="font-medium">Google Gemini</h5>
                  <p className="text-sm text-gray-600">API status: Active</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}