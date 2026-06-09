import { useState, useEffect } from 'react';
import { api } from '../services/api';

export default function PoseHistory({ userId, poseName }) {
  const [history, setHistory] = useState(null);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false); // must be before any early returns

  useEffect(() => {
    if (!userId || !poseName) return;
    
    const loadHistory = async () => {
      setLoading(true);
      try {
        const data = await api.getPoseHistory(userId, poseName);
        setHistory(data);
      } catch (err) {
        console.error("Failed to load history", err);
      } finally {
        setLoading(false);
      }
    };
    
    loadHistory();
  }, [userId, poseName]);

  if (loading) return <div style={{opacity: 0.5}}>Loading history...</div>;
  if (!history || history.attempts.length === 0) return null;

  return (
    <div className={`fb-benefits ${open ? 'fb-benefits--open' : ''}`} style={{marginTop: '24px'}}>
      <button className="fb-benefits__toggle" onClick={() => setOpen(o => !o)}>
        <span className="fb-benefits__icon">📊</span>
        <span className="fb-benefits__title">Your History: {history.pose_name}</span>
        {history.best_score && (
          <span className="score-badge score-correct" style={{fontSize: '0.78rem', padding: '4px 12px', marginRight: '8px'}}>
            Best: {history.best_score.toFixed(0)}
          </span>
        )}
        <span className={`fb-benefits__chevron ${open ? 'fb-benefits__chevron--open' : ''}`}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="6 9 12 15 18 9"/></svg>
        </span>
      </button>
      <div className="fb-benefits__body">
        <div style={{padding: '0 22px 18px', overflowX: 'auto'}}>
          <table className="history-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Score</th>
                <th>Assessment</th>
                <th>Type</th>
              </tr>
            </thead>
            <tbody>
              {history.attempts.map((attempt) => (
                <tr key={attempt.id}>
                  <td>{new Date(attempt.created_at).toLocaleDateString()} {new Date(attempt.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</td>
                  <td><strong style={{color: 'var(--primary-200)'}}>{attempt.overall_score.toFixed(0)}</strong></td>
                  <td>
                    <span style={{
                      color: attempt.correctness_label === 'correct' ? 'var(--success-400)' :
                             attempt.correctness_label === 'needs_adjustment' ? 'var(--warning-400)' :
                             attempt.correctness_label === 'incorrect' ? 'var(--danger-400)' : 'var(--text-muted)'
                    }}>
                      {attempt.correctness_label.replace('_', ' ')}
                    </span>
                  </td>
                  <td style={{textTransform: 'capitalize'}}>{attempt.input_type}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
