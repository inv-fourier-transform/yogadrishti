export default function Navbar() {
  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <div className="logo">YogaAI 🧘</div>
        <span className="tagline">Pose Detector</span>
      </div>
      <div className="navbar-links">
        <a href="/" className="active">Analyzer</a>
      </div>
    </nav>
  );
}
