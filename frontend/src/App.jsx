import { useState, useEffect, Component } from 'react';
import { api } from './services/api';
import Navbar from './components/Navbar';
import UserSelector from './components/UserSelector';
import FileUpload from './components/FileUpload';
import ResultCard from './components/ResultCard';
import PoseHistory from './components/PoseHistory';

/* ── Error Boundary: catches render crashes in ResultCard ── */
class ResultErrorBoundary extends Component {
  constructor(props) { super(props); this.state = { crashed: false, message: '' }; }
  static getDerivedStateFromError(err) { return { crashed: true, message: err?.message || 'Render error' }; }
  componentDidCatch(err) { console.error('[ResultCard crash]', err); }
  render() {
    if (this.state.crashed) {
      return (
        <div className="error-container" style={{padding:'20px',marginTop:'20px',background:'rgba(239,68,68,0.1)',borderRadius:'12px'}}>
          <div className="error-title">Display Error</div>
          <div className="error-message">Results received but could not be displayed ({this.state.message}). Please try again.</div>
          <button className="btn btn-secondary" style={{marginTop:'12px'}} onClick={this.props.onReset}>← Try Again</button>
        </div>
      );
    }
    return this.props.children;
  }
}

function App() {
  const [activeUser, setActiveUser] = useState(null);
  const [config, setConfig] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [imagePreview, setImagePreview] = useState(null); // persists across states

  useEffect(() => {
    const loadConfig = async () => {
      try {
        const conf = await api.getConfig();
        setConfig(conf);
      } catch (err) {
        console.error("Failed to load config", err);
      }
    };
    loadConfig();

    // Rehydrate user from local storage
    const savedUser = localStorage.getItem('yoga_user');
    if (savedUser) {
      try {
        setActiveUser(JSON.parse(savedUser));
      } catch (e) { /* ignore */ }
    }
  }, []);

  const handleUserSelect = (user) => {
    setActiveUser(user);
    if (user) {
      localStorage.setItem('yoga_user', JSON.stringify(user));
    } else {
      localStorage.removeItem('yoga_user');
    }
  };

  const handleUpload = async (file) => {
    setError(null);
    setResults(null);
    setIsAnalyzing(true);
    
    // Keep the image preview visible
    if (file.type.startsWith('image/')) {
      setImagePreview(URL.createObjectURL(file));
    }
    
    try {
      const response = await api.analyzeImage(file, activeUser?.id);
      
      if (response.status === 422) {
        let errMsg = "Upload validation failed.";
        if (response.data.detail) {
          if (typeof response.data.detail === 'string') errMsg = response.data.detail;
          else if (response.data.detail.message) errMsg = response.data.detail.message;
          else if (Array.isArray(response.data.detail)) errMsg = response.data.detail.map(d => d.msg || d.message).join(", ");
          else errMsg = JSON.stringify(response.data.detail);
        }
        setError(errMsg);
      } else if (response.status === 200) {
        const d = response.data;
        // Guard every numeric field — a null score crashes .toFixed()
        setResults({
          evaluation: {
            pose_name: d.pose_name || 'Unknown Pose',
            sanskrit_name: d.sanskrit_name || '',
            pose_confidence: d.pose_confidence ?? 0,
            evaluation_status: d.evaluation_status || '',
            overall_score: d.overall_score ?? 0,
            correctness_label: d.correctness_label || '',
            issues: d.issues || [],
            safety_flags: d.safety_flags || [],
            reliability_reason: d.reliability_reason || '',
            angles: d.angles || {},
          },
          feedbackText: d.feedback || '',
          comparison: d.progress || null,
        });
      } else {
        setError(response.data?.detail || response.data?.message || "An unexpected error occurred.");
      }
    } catch (err) {
      setError(err.message || "Failed to connect to the server.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleReset = () => {
    setResults(null);
    setError(null);
    setImagePreview(null);
  };

  return (
    <>
      <Navbar />
      
      <main className="container page">
        
        {/* User Selection Header */}
        <section className="user-section">
          <div>
            <span style={{color: 'var(--text-muted)', marginRight: '16px'}}>Profile:</span>
            <UserSelector 
              currentUser={activeUser} 
              onSelect={handleUserSelect} 
            />
          </div>
        </section>

        {/* Upload section — shown when no results */}
        {!results && !isAnalyzing && (
          <section className="hero">
            <h1>Yogadṛṣṭi (योगदृष्टि) — AI-Powered Pose Detector</h1>
            <p>Upload a photo of your yoga pose for instant AI-powered feedback on alignment and form.</p>
            
            <div style={{marginTop: '40px', maxWidth: '700px', margin: '40px auto 0'}}>
              <FileUpload 
                onUpload={handleUpload} 
                config={config} 
              />
            </div>
          </section>
        )}

        {/* Error banner — always visible, outside conditional blocks */}
        {error && !results && !isAnalyzing && (
          <div className="error-container" style={{padding: '20px', marginTop: '20px', maxWidth:'700px', margin:'20px auto 0', background: 'rgba(239,68,68,0.1)', borderRadius: '12px'}}>
            <div className="error-title">Analysis Failed</div>
            <div className="error-message">{error}</div>
          </div>
        )}

        {/* Analyzing State — image stays visible with spinner below */}
        {isAnalyzing && (
          <div className="fade-in" style={{maxWidth: '700px', margin: '0 auto'}}>
            {imagePreview && (
              <div style={{borderRadius: '12px', overflow: 'hidden', marginBottom: '24px', border: '2px solid var(--primary-500)', boxShadow: '0 0 20px rgba(139,92,246,0.15)'}}>
                <img src={imagePreview} alt="Uploaded pose" style={{width: '100%', display: 'block', maxHeight: '400px', objectFit: 'contain', background: 'var(--bg-surface)'}} />
              </div>
            )}
            <div className="loading-container" style={{marginTop: '20px'}}>
              <div className="spinner"></div>
              <h3 className="loading-text">Analyzing Pose...</h3>
              <p style={{color: 'var(--text-muted)', marginTop: '8px'}}>Extracting landmarks, evaluating alignment, and generating instructor feedback.</p>
            </div>
          </div>
        )}

        {/* Results View — image stays visible above results */}
        {results && (
          <div className="fade-in">
            <div style={{display: 'flex', justifyContent: 'flex-end', marginBottom: '20px'}}>
              <button className="btn btn-secondary" onClick={handleReset}>
                ← Analyze Another Pose
              </button>
            </div>

            {/* Uploaded image stays visible */}
            {imagePreview && (
              <div style={{borderRadius: '12px', overflow: 'hidden', marginBottom: '24px', maxWidth: '500px', margin: '0 auto 24px', border: '1px solid var(--border-subtle)'}}>
                <img src={imagePreview} alt="Analyzed pose" style={{width: '100%', display: 'block', maxHeight: '350px', objectFit: 'contain', background: 'var(--bg-surface)'}} />
              </div>
            )}

            {/* Error boundary catches any render crash inside ResultCard */}
            <ResultErrorBoundary onReset={handleReset}>
              <ResultCard 
                evaluation={results.evaluation} 
                feedback={results.feedbackText}
                comparison={results.comparison}
              />
            </ResultErrorBoundary>
            
            {activeUser && results?.evaluation?.pose_name && (
              <PoseHistory 
                userId={activeUser.id} 
                poseName={results.evaluation.pose_name} 
              />
            )}
          </div>
        )}

      </main>
    </>
  );
}

export default App;
