'use client';

import { useState } from 'react';
import { gameAPI, CreateGameRequest } from '@/lib/api';

interface GameCreatorProps {
  onGameCreated: (gameId: string) => void;
}

export default function GameCreator({ onGameCreated }: GameCreatorProps) {
  const [formData, setFormData] = useState({
    name: '',
    game_type: 'rpg',
    creator_id: 'user_123', // In real app, get from auth
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const gameTypes = [
    { value: 'rpg', label: 'RPG Adventure', description: 'Role-playing game with characters and quests' },
    { value: 'puzzle', label: 'Puzzle Game', description: 'Brain teasers and logic challenges' },
    { value: 'story', label: 'Interactive Story', description: 'Narrative-driven adventure' },
    { value: 'trivia', label: 'Trivia Quiz', description: 'Knowledge-based question game' },
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const request: CreateGameRequest = {
        ...formData,
        config: {
          modules: ['chatbot', 'state', 'rules'],
          difficulty: 'medium',
        },
      };

      const result = await gameAPI.createGame(request);
      onGameCreated(result.game_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create game');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold mb-6 text-gray-900">Create New Game</h2>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
            Game Name
          </label>
          <input
            type="text"
            id="name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Enter your game name"
            required
          />
        </div>

        <div>
          <label htmlFor="game_type" className="block text-sm font-medium text-gray-700 mb-2">
            Game Type
          </label>
          <select
            id="game_type"
            value={formData.game_type}
            onChange={(e) => setFormData({ ...formData, game_type: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {gameTypes.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
          <p className="text-sm text-gray-500 mt-1">
            {gameTypes.find(t => t.value === formData.game_type)?.description}
          </p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={isLoading}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isLoading ? 'Creating Game...' : 'Create Game'}
        </button>
      </form>
    </div>
  );
}