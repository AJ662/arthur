const API_BASE = 'http://localhost:8000';
const WS_BASE = 'ws://localhost:8000';

export interface GameConfig {
  game_type: string;
  [key: string]: any;
}

export interface CreateGameRequest {
  name: string;
  game_type: string;
  config: GameConfig;
  creator_id: string;
}

export interface ChatRequest {
  message: string;
  bot_id?: string;
  game_id?: string;
  player_id?: string;
}

export interface PlayerAction {
  type: string;
  player_id: string;
  [key: string]: any;
}

class GameAPI {
  async createGame(request: CreateGameRequest) {
    const response = await fetch(`${API_BASE}/games/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });
    
    if (!response.ok) {
      throw new Error('Failed to create game');
    }
    
    return response.json();
  }

  async sendChatMessage(request: ChatRequest) {
    const response = await fetch(`${API_BASE}/chat/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });
    
    if (!response.ok) {
      throw new Error('Failed to send message');
    }
    
    return response.json();
  }

  async sendPlayerAction(gameId: string, action: PlayerAction) {
    const response = await fetch(`${API_BASE}/games/${gameId}/action`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(action),
    });
    
    if (!response.ok) {
      throw new Error('Failed to send action');
    }
    
    return response.json();
  }

  // WebSocket connection for real-time events
  connectWebSocket(onMessage: (data: any) => void) {
    const ws = new WebSocket(`${WS_BASE}/ws`);
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      onMessage(data);
    };
    
    return ws;
  }
}

export const gameAPI = new GameAPI();