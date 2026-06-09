import { useState } from 'react';

export default function UserSelector({ currentUser, onSelect }) {
  const [mode, setMode] = useState(null); // null, 'register', 'login'
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleRegister = async (e) => {
    e.preventDefault();
    if (!name.trim() || !email.trim()) return;
    setError("");
    setIsLoading(true);
    try {
      const { api } = await import('../services/api');
      const user = await api.createUser(name.trim(), email.trim());
      onSelect(user);
      resetForm();
    } catch (err) {
      if (err.status === 409) {
        setError(err.message || "An account with this email already exists.");
      } else {
        setError(err.message || "Registration failed.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    if (!email.trim()) return;
    setError("");
    setIsLoading(true);
    try {
      const { api } = await import('../services/api');
      const user = await api.loginUser(email.trim());
      onSelect(user);
      resetForm();
    } catch (err) {
      if (err.status === 404) {
        setError("No account found with this email. Please register first.");
      } else {
        setError(err.message || "Login failed.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteProfile = async () => {
    if (!window.confirm("Are you sure? This will delete your profile and ALL activity history permanently.")) return;
    setIsLoading(true);
    try {
      const { api } = await import('../services/api');
      await api.deleteUser(currentUser.id);
      onSelect(null);
    } catch (err) {
      alert(err.message || "Failed to delete profile.");
    } finally {
      setIsLoading(false);
    }
  };

  const resetForm = () => {
    setName("");
    setEmail("");
    setMode(null);
    setError("");
  };

  // ── Logged-in state ──
  if (currentUser) {
    return (
      <div style={{display: 'inline-flex', alignItems: 'center', gap: '12px'}}>
        <div style={{fontWeight: '600', color: 'var(--primary-200)'}}>
          {currentUser.display_name}
          {currentUser.email && (
            <span style={{fontWeight: '400', color: 'var(--text-muted)', fontSize: '0.85em', marginLeft: '6px'}}>
              ({currentUser.email})
            </span>
          )}
        </div>
        <button
          className="btn btn-secondary btn-sm"
          onClick={() => onSelect(null)}
        >
          Logout
        </button>
        <button
          className="btn btn-sm"
          style={{background: 'var(--error)', color: 'white', border: 'none', padding: '4px 10px', borderRadius: '6px', cursor: 'pointer', fontSize: '0.8em'}}
          onClick={handleDeleteProfile}
          disabled={isLoading}
        >
          {isLoading ? "..." : "Delete Profile"}
        </button>
      </div>
    );
  }

  // ── No user — show mode selector ──
  if (!mode) {
    return (
      <div style={{display: 'inline-flex', gap: '8px'}}>
        <button className="btn btn-primary btn-sm" onClick={() => setMode('login')}>
          Login
        </button>
        <button className="btn btn-secondary btn-sm" onClick={() => setMode('register')}>
          Register
        </button>
      </div>
    );
  }

  // ── Login Form ──
  if (mode === 'login') {
    return (
      <form className="new-user-inline" onSubmit={handleLogin} style={{display: 'inline-flex', gap: '6px', alignItems: 'center'}}>
        <input
          type="email"
          className="new-user-input"
          placeholder="Your email..."
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          disabled={isLoading}
          autoFocus
          style={{minWidth: '200px'}}
        />
        <button type="submit" className="btn btn-primary btn-sm" disabled={isLoading || !email.trim()}>
          {isLoading ? "..." : "Login"}
        </button>
        <button type="button" className="btn btn-secondary btn-sm" onClick={resetForm}>
          Cancel
        </button>
        {error && <span style={{color: 'var(--error)', fontSize: '0.85em', marginLeft: '8px'}}>{error}</span>}
      </form>
    );
  }

  // ── Registration Form ──
  return (
    <form className="new-user-inline" onSubmit={handleRegister} style={{display: 'inline-flex', gap: '6px', alignItems: 'center', flexWrap: 'wrap'}}>
      <input
        type="text"
        className="new-user-input"
        placeholder="Your name..."
        value={name}
        onChange={(e) => setName(e.target.value)}
        disabled={isLoading}
        autoFocus
      />
      <input
        type="email"
        className="new-user-input"
        placeholder="Your email..."
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        disabled={isLoading}
        style={{minWidth: '200px'}}
      />
      <button type="submit" className="btn btn-primary btn-sm" disabled={isLoading || !name.trim() || !email.trim()}>
        {isLoading ? "..." : "Register"}
      </button>
      <button type="button" className="btn btn-secondary btn-sm" onClick={resetForm}>
        Cancel
      </button>
      {error && <span style={{color: 'var(--error)', fontSize: '0.85em', display: 'block', width: '100%', marginTop: '4px'}}>{error}</span>}
    </form>
  );
}
