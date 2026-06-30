import { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [gameId, setGameId] = useState(null);
  const [attempts, setAttempts] = useState(0);
  const [guess, setGuess] = useState('');
  const [clue, setClue] = useState('Digite um número de 1 a 100 para começar a adivinhar!');
  const [clueType, setClueType] = useState('neutral'); // neutral, high, low, correct
  const [history, setHistory] = useState([]);
  const [shake, setShake] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Fetch match history on mount
  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const response = await fetch('/api/game/history');
      if (response.ok) {
        const data = await response.json();
        setHistory(data);
      }
    } catch (error) {
      console.error('Erro ao buscar histórico:', error);
    }
  };

  const startNewGame = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/game/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      if (response.ok) {
        const data = await response.json();
        setGameId(data.game_id);
        setAttempts(0);
        setGuess('');
        setClue('Jogo iniciado! Tente adivinhar o número secreto de 1 a 100.');
        setClueType('neutral');
        // Refresh history to show new active game
        fetchHistory();
      }
    } catch (error) {
      console.error('Erro ao iniciar jogo:', error);
      setClue('Falha ao iniciar o jogo. Verifique a conexão.');
      setClueType('high');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGuessSubmit = async (e) => {
    e.preventDefault();
    if (!guess || isNaN(guess)) return;
    
    setIsLoading(true);
    try {
      const response = await fetch('/api/game/guess', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          game_id: gameId,
          guess: parseInt(guess, 10),
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setAttempts(data.attempts);
        
        if (data.status === 'completed') {
          setClue(`Parabéns! Você acertou o número secreto em ${data.attempts} tentativas.`);
          setClueType('correct');
        } else {
          // data.message will be "too high" or "too low"
          if (data.message === 'too high') {
            setClue('Muito alto! Tente um número menor. ⬆️');
            setClueType('high');
          } else {
            setClue('Muito baixo! Tente um número maior. ⬇️');
            setClueType('low');
          }
          // Trigger shake animation
          setShake(true);
          setTimeout(() => setShake(false), 400);
        }
        fetchHistory();
      }
    } catch (error) {
      console.error('Erro ao enviar palpite:', error);
      setClue('Erro ao processar palpite. Tente novamente.');
      setClueType('high');
    } finally {
      setIsLoading(false);
      setGuess('');
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleString('pt-BR', {
      hour: '2-digit',
      minute: '2-digit',
      day: '2-digit',
      month: '2-digit',
    });
  };

  return (
    <div className="app-container">
      {/* Sidebar - History */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <h2 className="sidebar-title">Painel de Jogos</h2>
          <p className="sidebar-desc">Acompanhe a atividade em tempo real</p>
        </div>
        <div className="history-section">
          <h3>Histórico de Partidas</h3>
          <div className="history-list">
            {history.length === 0 ? (
              <div className="empty-history">Nenhuma partida registrada</div>
            ) : (
              history.map((game) => (
                <div className="history-item" key={game.id}>
                  <div className="history-item-header">
                    <span className="game-id">ID: {game.id}</span>
                    <span className={`status-badge status-${game.status}`}>
                      {game.status === 'completed' ? 'Finalizado' : 'Ativo'}
                    </span>
                  </div>
                  <div className="history-details">
                    <div>
                      <span className="history-detail-label">Tentativas: </span>
                      <span className="history-detail-value">{game.attempts}</span>
                    </div>
                    {game.status === 'completed' && (
                      <div>
                        <span className="history-detail-label">Número: </span>
                        <span className="history-detail-value">{game.secret_number}</span>
                      </div>
                    )}
                  </div>
                  <div className="history-date">
                    {formatDate(game.completed_at || game.created_at)}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </aside>

      {/* Main Content - Guessing Game */}
      <main className="main-content">
        <div className="game-card">
          <div className="card-header">
            <h1 className="card-title">Guessing Game</h1>
            <p className="card-subtitle">Orquestrado com Docker, Flask, React & Postgres</p>
          </div>

          {!gameId ? (
            /* Lobby View */
            <div className="lobby-view">
              <span className="start-illustration">🎮</span>
              <button 
                className="btn-primary" 
                onClick={startNewGame}
                disabled={isLoading}
              >
                {isLoading ? 'Iniciando...' : 'Começar Novo Jogo'}
              </button>
            </div>
          ) : (
            /* Active Game View */
            <div className="active-game-view">
              <div className="game-metrics">
                <div className="metric-box">
                  <span className="metric-value">{attempts}</span>
                  <span className="metric-label">Tentativas</span>
                </div>
                <div className="metric-box">
                  <span className="metric-value">1 - 100</span>
                  <span className="metric-label">Intervalo</span>
                </div>
              </div>

              <div className={`clue-alert clue-alert-${clueType}`}>
                <span className="clue-icon">
                  {clueType === 'neutral' && '💡'}
                  {clueType === 'high' && '🔥'}
                  {clueType === 'low' && '❄️'}
                  {clueType === 'correct' && '🏆'}
                </span>
                <p>{clue}</p>
              </div>

              {clueType !== 'correct' ? (
                <form onSubmit={handleGuessSubmit} className="guess-input-group">
                  <input
                    type="number"
                    min="1"
                    max="100"
                    placeholder="Seu palpite"
                    className={`guess-input ${shake ? 'shake-input' : ''}`}
                    value={guess}
                    onChange={(e) => setGuess(e.target.value)}
                    disabled={isLoading}
                    required
                    autoFocus
                  />
                  <button 
                    type="submit" 
                    className="btn-guess" 
                    disabled={isLoading}
                  >
                    Palpitar
                  </button>
                </form>
              ) : (
                <div className="action-buttons">
                  <button 
                    className="btn-primary" 
                    onClick={startNewGame}
                    disabled={isLoading}
                  >
                    Jogar Novamente
                  </button>
                  <button 
                    className="btn-secondary" 
                    onClick={() => {
                      setGameId(null);
                      setAttempts(0);
                      setClue('Digite um número de 1 a 100 para começar a adivinhar!');
                      setClueType('neutral');
                    }}
                  >
                    Voltar ao Menu
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
